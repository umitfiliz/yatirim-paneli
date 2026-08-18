"""
BIST & ABD Yatırım Karar Destek Paneli
Katman 1: Makro Rejim | Katman 2: Varlık Sınıfı Kıyası | Katman 3: Hisse Seçimi

Çalıştırmak için: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

from config import (
    BIST_HISSELER,
    ABD_HISSELER,
    DIGER_VARLIKLAR,
    MAKRO_GOSTERGELER,
    POLITIKA_FAIZLERI_MANUEL,
    VADE_GUN,
    MAKRO_GOSTERGE_BILGI,
    FAIZ_GOSTERGE_BILGI,
    MANUEL_GEREKCE,
    KAYNAK_LINKLERI,
    DEFAULT_ESIKLER,
)
from data_utils import (
    fiyat_gecmisi_getir,
    getiri_hesapla,
    hisse_listesi_analiz_et,
    bist_listesi_usd_analiz_et,
    usd_try_kuru_getir,
    ortalama_getiri,
)
from macro_utils import tum_politika_faizlerini_getir, tcmb_tufe_yillik_getir
from country_utils import ortalama_fk_getir, dxy_getir, abd_tahvil_getir, tr_reel_faiz_hesapla
from regime_utils import (
    rejim_ozeti_olustur,
    tr_baglam_olustur,
    us_baglam_olustur,
    altin_baglam_olustur,
    mevduat_baglam_olustur,
    usdtry_baglam_olustur,
    momentum_skoru_hesapla,
    gorunum_olustur,
)
from kurumsal_gorunum import (
    KURUMSAL_GORUNUMLER,
    MEVCUT_SEVIYE_REFERANS,
    GUVEN_AGIRLIGI_ACIKLAMA,
    DERLEME_TARIHI as KURUMSAL_DERLEME_TARIHI,
)

st.set_page_config(
    page_title="Yatırım Karar Destek Paneli",
    layout="wide",
)

# Veri çekme fonksiyonlarını cache'liyoruz ki her sekme değişiminde
# yeniden indirmesin (1 saat boyunca aynı veriyi kullanır)
fiyat_gecmisi_getir_cached = st.cache_data(ttl=3600)(fiyat_gecmisi_getir)
hisse_listesi_analiz_et_cached = st.cache_data(ttl=3600)(hisse_listesi_analiz_et)
bist_listesi_usd_analiz_et_cached = st.cache_data(ttl=3600)(bist_listesi_usd_analiz_et)
usd_try_kuru_getir_cached = st.cache_data(ttl=3600)(usd_try_kuru_getir)

st.title("📊 Yatırım Karar Destek Paneli")
st.caption("BIST & ABD hisseleri | Getiriler USD bazlı | Bu bir karar destek aracıdır, yatırım tavsiyesi değildir.")
st.caption(
    f"🕒 Sayfa son yüklenme zamanı: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')} "
    "— ham veriler en fazla 1 saat önbellekte tutulur, bu yüzden gösterilen değerler "
    "bu zaman damgasından biraz daha eski olabilir."
)

# ============================================================
# KENAR ÇUBUĞU: Rejim yorumlama katmanının eşik değerlerini ayarla
# ============================================================
with st.sidebar:
    st.header("⚙️ Karar Mekanizması Ayarları")
    st.caption(
        "Aşağıdaki eşik değerleri, Katman 1'deki 'Rejim Özeti' ve 'Ülkeye Özgü "
        "Faktörler' bölümlerinin nasıl yorumlandığını belirler. Varsayılan "
        "değerler makul bir başlangıç noktasıdır, kendi görüşüne göre ayarlayabilirsin."
    )

    with st.expander("Risk İştahı (VIX)"):
        vix_risk_on = st.slider("Risk-On eşiği (altı)", 10.0, 30.0, DEFAULT_ESIKLER["vix_risk_on"], 0.5, key="esik_vix_risk_on")
        vix_risk_off = st.slider("Risk-Off eşiği (üstü)", 20.0, 50.0, DEFAULT_ESIKLER["vix_risk_off"], 0.5, key="esik_vix_risk_off")

    with st.expander("Sermaye Akışı & DXY"):
        sermaye_esik = st.slider("Sermaye akışı %değişim eşiği", 0.5, 10.0, DEFAULT_ESIKLER["sermaye_esik"], 0.5, key="esik_sermaye")
        dxy_esik = st.slider("DXY %değişim eşiği", 0.5, 10.0, DEFAULT_ESIKLER["dxy_esik"], 0.5, key="esik_dxy")

    with st.expander("Carry Cazibesi (TCMB-Fed Farkı)"):
        carry_yuksek = st.slider("Yüksek eşiği (puan)", 0.0, 30.0, DEFAULT_ESIKLER["carry_yuksek"], 1.0, key="esik_carry_yuksek")
        carry_cok_yuksek = st.slider("Çok Yüksek eşiği (puan)", 5.0, 50.0, DEFAULT_ESIKLER["carry_cok_yuksek"], 1.0, key="esik_carry_cok_yuksek")

    with st.expander("Değerleme (F/K Oranı)"):
        bist_fk_ucuz = st.slider("BIST 'Ucuz' eşiği (F/K altı)", 3.0, 20.0, DEFAULT_ESIKLER["bist_fk_ucuz"], 0.5, key="esik_bist_fk_ucuz")
        bist_fk_pahali = st.slider("BIST 'Pahalı' eşiği (F/K üstü)", 8.0, 30.0, DEFAULT_ESIKLER["bist_fk_pahali"], 0.5, key="esik_bist_fk_pahali")
        abd_fk_ucuz = st.slider("ABD 'Ucuz' eşiği (F/K altı)", 10.0, 35.0, DEFAULT_ESIKLER["abd_fk_ucuz"], 0.5, key="esik_abd_fk_ucuz")
        abd_fk_pahali = st.slider("ABD 'Pahalı' eşiği (F/K üstü)", 20.0, 50.0, DEFAULT_ESIKLER["abd_fk_pahali"], 0.5, key="esik_abd_fk_pahali")

    with st.expander("Fed Faiz Yönü & ABD Tahvili"):
        fed_yon_esik = st.slider("Fed faiz yönü eşiği (puan)", 0.05, 1.0, DEFAULT_ESIKLER["fed_yon_esik"], 0.05, key="esik_fed_yon")
        tahvil_esik = st.slider("ABD 10Y tahvil %değişim eşiği", 1.0, 10.0, DEFAULT_ESIKLER["tahvil_esik"], 0.5, key="esik_tahvil")

    with st.expander("3-6 Aylık Görünüm (Momentum)"):
        momentum_esik = st.slider(
            "Momentum %değişim eşiği (son 3 ay)", 0.5, 10.0, DEFAULT_ESIKLER["momentum_esik"], 0.5, key="esik_momentum"
        )

    if st.button("↺ Varsayılanlara Sıfırla"):
        for k in list(DEFAULT_ESIKLER.keys()):
            st.session_state.pop(f"esik_{k}", None)
        st.rerun()

    esikler = {
        "vix_risk_on": vix_risk_on,
        "vix_risk_off": vix_risk_off,
        "sermaye_esik": sermaye_esik,
        "carry_yuksek": carry_yuksek,
        "carry_cok_yuksek": carry_cok_yuksek,
        "bist_fk_ucuz": bist_fk_ucuz,
        "bist_fk_pahali": bist_fk_pahali,
        "abd_fk_ucuz": abd_fk_ucuz,
        "abd_fk_pahali": abd_fk_pahali,
        "dxy_esik": dxy_esik,
        "tahvil_esik": tahvil_esik,
        "fed_yon_esik": fed_yon_esik,
        "momentum_esik": momentum_esik,
    }

sekme1, sekme2, sekme3 = st.tabs([
    "🌍 Katman 1: Makro Rejim",
    "⚖️ Katman 2: Varlık Sınıfı Kıyası",
    "📈 Katman 3: Hisse Seçimi",
])

# ============================================================
# KATMAN 1: MAKRO REJİM
# ============================================================
with sekme1:
    st.subheader("Küresel Makro Göstergeler")
    st.write("Risk iştahı ve sermaye akış yönünü özetleyen göstergeler.")

    kolonlar = st.columns(3)
    makro_degerler = {}  # rejim özeti hesaplamasında tekrar kullanmak için sakla
    for i, (ticker, isim) in enumerate(MAKRO_GOSTERGELER.items()):
        veri = fiyat_gecmisi_getir_cached(ticker, gun_sayisi=60)
        with kolonlar[i % 3]:
            if not veri.empty:
                guncel = float(veri["Close"].dropna().iloc[-1])
                degisim_7g = getiri_hesapla(veri, 7)
                degisim_30g = getiri_hesapla(veri, 30)
                makro_degerler[isim] = {"guncel": guncel, "degisim_7g": degisim_7g, "degisim_30g": degisim_30g}
                st.metric(
                    label=isim,
                    value=f"{guncel:,.2f}",
                    delta=f"{degisim_7g}% (7 gün)" if degisim_7g is not None else None,
                    help=MAKRO_GOSTERGE_BILGI.get(isim),
                )
            else:
                st.warning(f"{isim} verisi çekilemedi")

    st.divider()
    st.subheader("Politika Faizleri")

    fred_key = st.secrets.get("FRED_API_KEY", "")
    # TCMB politika faizi artık key gerektirmiyor (borsapy üzerinden çekiliyor),
    # bu yüzden en azından TCMB satırı FRED key'i olmasa bile otomatik gelebilir.
    tum_politika_faizlerini_getir_cached = st.cache_data(ttl=3600)(tum_politika_faizlerini_getir)
    otomatik_faizler = tum_politika_faizlerini_getir_cached(fred_key)

    # Katman 2'nin TL mevduat yaklaşık getirisi hesaplayabilmesi için sakla
    st.session_state["tcmb_faiz_guncel"] = otomatik_faizler.get("TCMB Faiz Oranı (%)") or POLITIKA_FAIZLERI_MANUEL.get("TCMB Faiz Oranı (%)")

    faiz_satirlari = []
    for isim, deger in otomatik_faizler.items():
        if deger is not None:
            faiz_satirlari.append({
                "Gösterge": isim, "Değer (%)": deger, "Kaynak": "Otomatik (API)", "Not": "—",
            })
        else:
            # API'den veri gelmezse manuel yedek değere düş
            manuel_deger = POLITIKA_FAIZLERI_MANUEL.get(isim)
            faiz_satirlari.append({
                "Gösterge": isim,
                "Değer (%)": manuel_deger,
                "Kaynak": "Manuel (yedek)" if manuel_deger else "Veri yok",
                "Not": MANUEL_GEREKCE.get(isim, "—"),
            })

    faiz_df = pd.DataFrame(faiz_satirlari)
    st.dataframe(
        faiz_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Not": st.column_config.TextColumn(
                "Not", help="Değer manuelse, otomatik çekilemeyişinin kısa gerekçesi."
            ),
        },
    )

    if not fred_key:
        st.warning(
            "FRED API key'i secrets.toml içinde bulunamadı — Fed, ECB, PBOC, BOJ satırları "
            "için manuel değerler gösteriliyor. TCMB satırı key gerektirmediği için "
            "otomatik gelmiş olmalı. README'deki kurulum adımlarını takip ederek FRED "
            "key'ini ekleyebilirsin."
        )

    st.caption(
        "'Otomatik (API)' etiketli değerler FRED/TCMB'den canlı çekilmiştir. "
        "Kaynak geçici olarak yanıt vermezse 'Manuel (yedek)' değer gösterilir — "
        "sebebi 'Not' sütununda belirtilir."
    )

    with st.expander("ℹ️ Bu göstergeler ne anlama geliyor? (yorumlama rehberi)"):
        for isim in FAIZ_GOSTERGE_BILGI:
            st.markdown(f"**{isim}**")
            st.markdown(FAIZ_GOSTERGE_BILGI[isim])
            st.markdown("---")

    with st.expander("🔗 Bu değerleri kendim nereden doğrulayabilirim?"):
        st.caption("Aşağıdaki resmi kaynaklardan güncel değerleri kendi gözünle kontrol edebilirsin.")
        for isim, url in KAYNAK_LINKLERI.items():
            st.markdown(f"- **{isim}:** [{url}]({url})")

    # ============================================================
    # REJİM ÖZETİ: Yukarıdaki ham verileri yorumlayıp tek bir bağlama dönüştür
    # ============================================================
    st.divider()
    st.subheader("🧭 Rejim Özeti")
    st.caption(
        "Yukarıdaki ham göstergelerin basit kural tabanlı bir yorumu. "
        "Kesin öngörü değildir, tarihsel genellemelere dayanır — Katman 2'ye bağlam olarak aktarılır."
    )

    vix_bilgi = makro_degerler.get("VIX (Risk İştahı)", {})
    usdtry_bilgi = makro_degerler.get("USD/TRY", {})
    usdcny_bilgi = makro_degerler.get("USD/CNY", {})

    rejim = rejim_ozeti_olustur(
        vix_guncel=vix_bilgi.get("guncel"),
        vix_degisim_7g=vix_bilgi.get("degisim_7g"),
        usdtry_degisim_30g=usdtry_bilgi.get("degisim_30g"),
        usdcny_degisim_30g=usdcny_bilgi.get("degisim_30g"),
        tcmb_faiz=otomatik_faizler.get("TCMB Faiz Oranı (%)") or POLITIKA_FAIZLERI_MANUEL.get("TCMB Faiz Oranı (%)"),
        fed_faiz=otomatik_faizler.get("Fed Faiz Oranı (%)") or POLITIKA_FAIZLERI_MANUEL.get("Fed Faiz Oranı (%)"),
        fred_api_key=fred_key,
        esikler=esikler,
    )

    # Katman 2'nin okuyabilmesi için session_state'e kaydet
    st.session_state["rejim_ozeti"] = rejim

    st.markdown(f"### Genel Rejim: **{rejim['genel_rejim']}**")

    # Bileşen dökümü: hangi göstergenin hangi yöne çektiğini şeffaf şekilde göster
    dokum_satirlari = []
    for kalem in rejim["dokum"]:
        skor = kalem["skor"]
        if skor is None:
            yon_ikonu = "❔"
        elif skor > 0:
            yon_ikonu = "🟢 Destekleyici"
        elif skor < 0:
            yon_ikonu = "🔴 Temkinli"
        else:
            yon_ikonu = "⚪ Nötr"
        dokum_satirlari.append({"Bileşen": kalem["bilesen"], "Durum": kalem["etiket"], "Yön": yon_ikonu})

    st.dataframe(pd.DataFrame(dokum_satirlari), use_container_width=True, hide_index=True)
    st.caption(
        "Genel rejim, yukarıdaki bileşenlerin ortalamasından türetilir. Bileşenler "
        "birbirine zıt yöne işaret ediyorsa (örn. biri destekleyici, diğeri temkinli), "
        "bu genellikle piyasanın henüz net bir yön bulamadığı veya birden fazla "
        "faktörün çekişme halinde olduğu bir dönemi işaret eder."
    )

    ozet_kolonlar = st.columns(2)
    with ozet_kolonlar[0]:
        st.markdown(f"**Risk İştahı:** {rejim['risk_istahi']['etiket']}")
        st.caption(rejim['risk_istahi']['aciklama'])
        st.markdown(f"**Fed Faiz Yönü:** {rejim['fed_faiz_yonu']['etiket']}")
        st.caption(rejim['fed_faiz_yonu']['aciklama'])
    with ozet_kolonlar[1]:
        st.markdown(f"**TL/EM Sermaye Akışı:** {rejim['sermaye_akisi']['etiket']}")
        st.caption(rejim['sermaye_akisi']['aciklama'])
        if rejim['carry_cazibesi']['etiket']:
            st.markdown(f"**TL Carry Cazibesi:** {rejim['carry_cazibesi']['etiket']}")
            st.caption(rejim['carry_cazibesi']['aciklama'])

    with st.expander("🔍 Karar Mekanizması Nasıl Çalışıyor? (güncel ayarlarınla)"):
        st.markdown(f"""
Her bileşen, aşağıdaki **şu anki eşik değerlerine** göre -1 (temkinli), 0 (nötr) veya
+1 (destekleyici) puan alır. Bu puanların ortalaması genel etiketi belirler. Eşikleri
kenar çubuğundaki (sol taraf) "⚙️ Karar Mekanizması Ayarları" bölümünden değiştirebilirsin.

**Risk İştahı (VIX):**
- VIX < {esikler['vix_risk_on']:.1f} → Risk-On → **+1**
- {esikler['vix_risk_on']:.1f} ≤ VIX < {esikler['vix_risk_off']:.1f} → Nötr → **0**
- VIX ≥ {esikler['vix_risk_off']:.1f} → Risk-Off → **-1**

**TL/EM Sermaye Akışı (USD/TRY ve USD/CNY ortalama 30 günlük %değişim):**
- Ortalama < -{esikler['sermaye_esik']:.1f}% → Sermaye Girişi → **+1**
- -{esikler['sermaye_esik']:.1f}% ile +{esikler['sermaye_esik']:.1f}% arası → Nötr → **0**
- Ortalama > +{esikler['sermaye_esik']:.1f}% → Sermaye Çıkışı → **-1**

**Fed Faiz Yönü (son ~90 gündeki puan değişimi):**
- Değişim < -{esikler['fed_yon_esik']:.2f} puan → Gevşiyor → **+1**
- -{esikler['fed_yon_esik']:.2f} ile +{esikler['fed_yon_esik']:.2f} puan arası → Sabit → **0**
- Değişim > +{esikler['fed_yon_esik']:.2f} puan → Sıkılaşıyor → **-1**

**Genel Rejim Skalası (ortalama puan → etiket):**
- ≥ 0.6 → Destekleyici
- 0.2 ile 0.6 arası → Ilımlı Destekleyici
- -0.2 ile 0.2 arası → Nötr / Yatay
- -0.6 ile -0.2 arası → Ilımlı Temkinli
- ≤ -0.6 → Temkinli / Savunmacı

Bileşenler arasındaki fark 2 puana ulaşırsa (örn. biri +1, diğeri -1), etikete
"bileşenler arasında çelişki var" notu eklenir — bu, tek bir yön göstergesine
güvenmemen gerektiğinin bir işaretidir.
        """)

    # ============================================================
    # ÜLKEYE ÖZGÜ FAKTÖRLER: Küresel resmin yakalayamadığı yerel dinamikler
    # ============================================================
    st.divider()
    st.subheader("🗺️ Ülkeye Özgü Faktörler")
    st.caption(
        "Küresel risk iştahı olumlu olsa bile, bir piyasanın kendi değerleme seviyesi "
        "veya reel faiz ortamı farklı bir tablo çizebilir. Bu bölüm iki piyasayı "
        "(BIST ve ABD) ayrı ayrı değerlendirir."
    )

    evds_key_tufe = st.secrets.get("EVDS_API_KEY", "")

    ulke_kolonlar = st.columns(2)

    # --- Türkiye'ye özgü faktörler ---
    with ulke_kolonlar[0]:
        st.markdown("#### 🇹🇷 Türkiye")

        tufe_yillik_cached = st.cache_data(ttl=3600)(tcmb_tufe_yillik_getir)
        tufe_yillik = tufe_yillik_cached(evds_key_tufe) if evds_key_tufe else None

        tcmb_faiz_deger = otomatik_faizler.get("TCMB Faiz Oranı (%)") or POLITIKA_FAIZLERI_MANUEL.get("TCMB Faiz Oranı (%)")
        reel_faiz = tr_reel_faiz_hesapla(tcmb_faiz_deger, tufe_yillik)

        ortalama_fk_getir_cached = st.cache_data(ttl=3600)(ortalama_fk_getir)
        bist_ort_fk = ortalama_fk_getir_cached(BIST_HISSELER)

        dxy_getir_cached = st.cache_data(ttl=3600)(dxy_getir)
        dxy_bilgi = dxy_getir_cached()

        tr_tablo = pd.DataFrame([
            {"Gösterge": "TÜFE Yıllık Enflasyon (%)", "Değer": f"{tufe_yillik:.1f}" if tufe_yillik is not None else "Veri yok (EVDS key gerekli)"},
            {"Gösterge": "Yaklaşık Reel Faiz (%)", "Değer": f"{reel_faiz:.1f}" if reel_faiz is not None else "Hesaplanamadı"},
            {"Gösterge": "BIST Ort. F/K (izlenen hisseler)", "Değer": f"{bist_ort_fk:.1f}" if bist_ort_fk is not None else "Veri yok"},
        ])
        st.dataframe(tr_tablo, use_container_width=True, hide_index=True)

        tr_baglam = tr_baglam_olustur(
            reel_faiz=reel_faiz,
            bist_ortalama_fk=bist_ort_fk,
            dxy_degisim_30g=dxy_bilgi.get("degisim_30g"),
            carry_etiket=rejim["carry_cazibesi"]["etiket"],
            esikler=esikler,
        )
        st.markdown(f"**BIST Bağlamı: {tr_baglam['genel_baglam']}**")

    # --- ABD'ye özgü faktörler ---
    with ulke_kolonlar[1]:
        st.markdown("#### 🇺🇸 ABD")

        abd_ort_fk_cached = st.cache_data(ttl=3600)(ortalama_fk_getir)
        abd_ort_fk = abd_ort_fk_cached(ABD_HISSELER)

        abd_tahvil_getir_cached = st.cache_data(ttl=3600)(abd_tahvil_getir)
        tahvil_bilgi = abd_tahvil_getir_cached()

        us_tablo = pd.DataFrame([
            {"Gösterge": "ABD Ort. F/K (izlenen hisseler)", "Değer": f"{abd_ort_fk:.1f}" if abd_ort_fk is not None else "Veri yok"},
            {"Gösterge": "10 Yıllık Tahvil Faizi (%)", "Değer": f"{tahvil_bilgi.get('guncel'):.2f}" if tahvil_bilgi.get("guncel") is not None else "Veri yok"},
            {"Gösterge": "Dolar Endeksi (DXY)", "Değer": f"{dxy_bilgi.get('guncel'):.2f}" if dxy_bilgi.get("guncel") is not None else "Veri yok"},
        ])
        st.dataframe(us_tablo, use_container_width=True, hide_index=True)

        us_baglam = us_baglam_olustur(
            fed_yon_etiket=rejim["fed_faiz_yonu"]["etiket"],
            abd_ortalama_fk=abd_ort_fk,
            tnx_degisim_30g=tahvil_bilgi.get("degisim_30g"),
            esikler=esikler,
        )
        st.markdown(f"**ABD Bağlamı: {us_baglam['genel_baglam']}**")

    st.caption(
        "Not: F/K değerleme eşikleri basit sezgisel aralıklardır (kesin tarihsel "
        "ortalamaya dayanmaz), yorumlarken bunu göz önünde bulundur."
    )

    with st.expander("🔍 BIST/ABD Bağlamları Nasıl Hesaplanıyor? (güncel ayarlarınla)"):
        st.markdown(f"""
**BIST Bağlamı bileşenleri:**
- TL Reel Faizi: ≥5 → Güçlü Pozitif (+1) · 0-5 → Hafif Pozitif (0) · <0 → Negatif (-1)
- BIST Ort. F/K: <{esikler['bist_fk_ucuz']:.1f} → Ucuz/Makul (+1) · {esikler['bist_fk_ucuz']:.1f}-{esikler['bist_fk_pahali']:.1f} → Makul (0) · >{esikler['bist_fk_pahali']:.1f} → Pahalı (-1)
- DXY Etkisi: değişim > +{esikler['dxy_esik']:.1f}% → Baskı (-1) · aralıkta → Nötr (0) · < -{esikler['dxy_esik']:.1f}% → Destek (+1)
- Carry Cazibesi: Yüksek/Çok Yüksek → +1 · Orta/Düşük → 0

**ABD Bağlamı bileşenleri:**
- Fed Faiz Yönü: Gevşiyor (+1) · Sabit (0) · Sıkılaşıyor (-1)
- ABD Ort. F/K: <{esikler['abd_fk_ucuz']:.1f} → Ucuz/Makul (+1) · {esikler['abd_fk_ucuz']:.1f}-{esikler['abd_fk_pahali']:.1f} → Makul (0) · >{esikler['abd_fk_pahali']:.1f} → Pahalı (-1)
- 10Y Tahvil Trendi: değişim > +{esikler['tahvil_esik']:.1f}% → Değerleme Baskısı (-1) · aralıkta → Stabil (0) · < -{esikler['tahvil_esik']:.1f}% → Değerleme Desteği (+1)

Bileşenlerin ortalaması aynı Genel Rejim skalasıyla (yukarıda) etikete dönüştürülür.
Eşikleri kenar çubuğundan değiştirebilirsin.

TÜFE verisini kendi gözünle doğrulamak istersen: [{KAYNAK_LINKLERI['TÜFE Yıllık Enflasyon (%)']}]({KAYNAK_LINKLERI['TÜFE Yıllık Enflasyon (%)']})
        """)

    # Katman 2'nin kullanabilmesi için ikisini de session_state'e kaydet
    st.session_state["tr_baglam"] = tr_baglam
    st.session_state["us_baglam"] = us_baglam

# ============================================================
# KATMAN 2: VARLIK SINIFI KIYASI
# ============================================================
with sekme2:
    st.subheader("Varlık Sınıfları Arası Getiri Kıyası (USD Bazlı)")

    rejim = st.session_state.get("rejim_ozeti")
    tr_baglam = st.session_state.get("tr_baglam")
    us_baglam = st.session_state.get("us_baglam")

    if rejim and tr_baglam and us_baglam:
        st.info(
            f"**Küresel Genel Rejim: {rejim['genel_rejim']}**\n\n"
            f"🇹🇷 **BIST Bağlamı: {tr_baglam['genel_baglam']}** — "
            f"Reel Faiz: {tr_baglam['reel_faiz']['etiket']} · "
            f"Değerleme: {tr_baglam['degerleme']['etiket']}\n\n"
            f"🇺🇸 **ABD Bağlamı: {us_baglam['genel_baglam']}** — "
            f"Değerleme: {us_baglam['degerleme']['etiket']} · "
            f"Tahvil Trendi: {us_baglam['tahvil']['etiket']}\n\n"
            "Bu bağlamları, aşağıdaki varlık sınıfı getirilerini yorumlarken göz önünde "
            "bulundurabilirsin — küresel resim olumlu olsa bile bir piyasanın kendi "
            "değerleme/reel faiz koşulları farklı bir tablo çizebilir."
        )
    else:
        st.caption(
            "Rejim ve ülke bağlamlarını görmek için önce Katman 1 sekmesini bir kez ziyaret et."
        )

    # ============================================================
    # ANA KARŞILAŞTIRMA: Hangi yatırım aracı daha avantajlı?
    # ============================================================
    varlik_sonuclari = hisse_listesi_analiz_et_cached(DIGER_VARLIKLAR, VADE_GUN)

    st.subheader("🏁 Varlık Sınıfı Karşılaştırması (USD Bazlı, Yaklaşık Getiri)")
    st.caption(
        "BIST hisseleri, ABD hisseleri, altın, TL mevduatı ve USD/TRY referansının "
        "aynı zaman dilimindeki (3 ve 6 ay) USD bazlı getirileri. Farklı risk "
        "profillerine sahip araçları aynı çizgide gösterir — geçmiş getiri gelecek "
        "performansın garantisi değildir."
    )

    # BIST ortalaması (USD bazlı)
    bist_karsilastirma = bist_listesi_usd_analiz_et_cached(BIST_HISSELER, VADE_GUN)
    bist_3ay = ortalama_getiri(bist_karsilastirma, "Getiri (3 Ay, USD)")
    bist_6ay = ortalama_getiri(bist_karsilastirma, "Getiri (6 Ay, USD)")

    # ABD ortalaması
    abd_karsilastirma = hisse_listesi_analiz_et_cached(ABD_HISSELER, VADE_GUN)
    abd_3ay = ortalama_getiri(abd_karsilastirma, "Getiri (3 Ay)")
    abd_6ay = ortalama_getiri(abd_karsilastirma, "Getiri (6 Ay)")

    # Altın (zaten varlik_sonuclari'nda var, DIGER_VARLIKLAR'dan)
    altin_satiri = varlik_sonuclari[varlik_sonuclari["Ticker"] == "GC=F"]
    altin_3ay = float(altin_satiri["Getiri (3 Ay)"].iloc[0]) if not altin_satiri.empty and pd.notna(altin_satiri["Getiri (3 Ay)"].iloc[0]) else None
    altin_6ay = float(altin_satiri["Getiri (6 Ay)"].iloc[0]) if not altin_satiri.empty and pd.notna(altin_satiri["Getiri (6 Ay)"].iloc[0]) else None

    # TL mevduatı — basit faiz yaklaşımıyla yıllık TCMB faizinden 3/6 aylık nominal
    # TL getirisi türetilip, aynı dönemdeki USD/TRY değişimi düşülerek USD bazına çevrilir.
    # Bu BİLEŞİK FAİZ DEĞİL, basit bir yaklaşımdır — gerçek mevduat ürünlerinde vade, stopaj
    # ve bankaya göre farklılık gösterebilir.
    tcmb_faiz_guncel = st.session_state.get("tcmb_faiz_guncel")
    usdtry_veri_200g = fiyat_gecmisi_getir_cached("TRY=X", gun_sayisi=200)
    usdtry_3ay_degisim = getiri_hesapla(usdtry_veri_200g, 90)
    usdtry_6ay_degisim = getiri_hesapla(usdtry_veri_200g, 180)

    if tcmb_faiz_guncel is not None:
        tl_mevduat_3ay_tl = round(tcmb_faiz_guncel * 90 / 365, 2)
        tl_mevduat_6ay_tl = round(tcmb_faiz_guncel * 180 / 365, 2)
        tl_mevduat_3ay_usd = round(tl_mevduat_3ay_tl - usdtry_3ay_degisim, 2) if usdtry_3ay_degisim is not None else None
        tl_mevduat_6ay_usd = round(tl_mevduat_6ay_tl - usdtry_6ay_degisim, 2) if usdtry_6ay_degisim is not None else None
    else:
        tl_mevduat_3ay_usd = None
        tl_mevduat_6ay_usd = None

    # USD/TRY referansı (sadece dolar tutmanın TL'ye göre getirisi)
    usdtry_referans_3ay = usdtry_3ay_degisim
    usdtry_referans_6ay = usdtry_6ay_degisim

    # ============================================================
    # 3-6 AYLIK GÖRÜNÜM: Momentum + Katman 1 bağlamını birleştiren
    # şeffaf, kural tabanlı yönelim etiketi (İSTATİSTİKSEL TAHMİN DEĞİLDİR)
    # ============================================================
    dxy_etiket_ref = tr_baglam["dxy"]["etiket"] if tr_baglam else "Bilinmiyor"
    risk_etiket_ref = rejim["risk_istahi"]["etiket"] if rejim else "Bilinmiyor"
    carry_etiket_ref = rejim["carry_cazibesi"]["etiket"] if rejim else None
    sermaye_etiket_ref = rejim["sermaye_akisi"]["etiket"] if rejim else "Bilinmiyor"

    altin_baglam = altin_baglam_olustur(risk_etiket_ref, dxy_etiket_ref)
    mevduat_baglam = mevduat_baglam_olustur(carry_etiket_ref)
    usdtry_baglam = usdtry_baglam_olustur(sermaye_etiket_ref)

    gorunum_bist, _ = gorunum_olustur(
        momentum_skoru_hesapla(bist_3ay, esikler["momentum_esik"]),
        tr_baglam.get("ortalama_skor") if tr_baglam else None,
    )
    gorunum_abd, _ = gorunum_olustur(
        momentum_skoru_hesapla(abd_3ay, esikler["momentum_esik"]),
        us_baglam.get("ortalama_skor") if us_baglam else None,
    )
    gorunum_altin, _ = gorunum_olustur(
        momentum_skoru_hesapla(altin_3ay, esikler["momentum_esik"]),
        altin_baglam.get("ortalama_skor"),
    )
    gorunum_mevduat, _ = gorunum_olustur(
        momentum_skoru_hesapla(tl_mevduat_3ay_usd, esikler["momentum_esik"]),
        mevduat_baglam.get("ortalama_skor"),
    )
    gorunum_usdtry, _ = gorunum_olustur(
        momentum_skoru_hesapla(usdtry_referans_3ay, esikler["momentum_esik"]),
        usdtry_baglam.get("ortalama_skor"),
    )

    karsilastirma_df = pd.DataFrame([
        {"Varlık": "BIST Hisseleri (Ort.)", "Getiri (3 Ay)": bist_3ay, "Getiri (6 Ay)": bist_6ay, "Görünüm (3-6 Ay)": gorunum_bist},
        {"Varlık": "ABD Hisseleri (Ort.)", "Getiri (3 Ay)": abd_3ay, "Getiri (6 Ay)": abd_6ay, "Görünüm (3-6 Ay)": gorunum_abd},
        {"Varlık": "Altın", "Getiri (3 Ay)": altin_3ay, "Getiri (6 Ay)": altin_6ay, "Görünüm (3-6 Ay)": gorunum_altin},
        {"Varlık": "TL Mevduatı (yaklaşık)", "Getiri (3 Ay)": tl_mevduat_3ay_usd, "Getiri (6 Ay)": tl_mevduat_6ay_usd, "Görünüm (3-6 Ay)": gorunum_mevduat},
        {"Varlık": "USD/TRY (referans)", "Getiri (3 Ay)": usdtry_referans_3ay, "Getiri (6 Ay)": usdtry_referans_6ay, "Görünüm (3-6 Ay)": gorunum_usdtry},
    ])

    # Sıralama: 3 aylık getiriye göre büyükten küçüğe
    karsilastirma_siralanmis = karsilastirma_df.dropna(subset=["Getiri (3 Ay)"]).sort_values(
        "Getiri (3 Ay)", ascending=False
    ).reset_index(drop=True)

    if not karsilastirma_siralanmis.empty:
        lider = karsilastirma_siralanmis.iloc[0]
        sonuncu = karsilastirma_siralanmis.iloc[-1]
        st.markdown(
            f"**🥇 Son 3 ayda en yüksek USD bazlı getiri: {lider['Varlık']} "
            f"(%{lider['Getiri (3 Ay)']:.1f})** · "
            f"En düşük: {sonuncu['Varlık']} (%{sonuncu['Getiri (3 Ay)']:.1f})"
        )

    st.dataframe(
        karsilastirma_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Getiri (3 Ay)": st.column_config.NumberColumn("Getiri (3 Ay)", help="Geçmiş 3 aylık gerçekleşen getiri.", format="%.2f%%"),
            "Getiri (6 Ay)": st.column_config.NumberColumn("Getiri (6 Ay)", help="Geçmiş 6 aylık gerçekleşen getiri.", format="%.2f%%"),
            "Görünüm (3-6 Ay)": st.column_config.TextColumn(
                "Görünüm (3-6 Ay)",
                help="Momentum + Katman 1 bağlamına dayanan kural tabanlı yönelim etiketi. SAYISAL BİR TAHMİN DEĞİLDİR.",
            ),
        },
    )

    # Grafik: gruplu çubuk grafik ile 3/6 aylık getirileri yan yana göster
    grafik_df = karsilastirma_df.dropna(subset=["Getiri (3 Ay)", "Getiri (6 Ay)"], how="all").melt(
        id_vars="Varlık", value_vars=["Getiri (3 Ay)", "Getiri (6 Ay)"],
        var_name="Vade", value_name="Getiri (%)"
    )
    if not grafik_df.empty:
        fig = px.bar(
            grafik_df, x="Varlık", y="Getiri (%)", color="Vade", barmode="group",
            title="Varlık Sınıfları USD Bazlı Getiri Karşılaştırması",
        )
        fig.update_layout(legend_title_text="", xaxis_title="", height=400)
        st.plotly_chart(fig, use_container_width=True)

    with st.expander("🔮 'Görünüm (3-6 Ay)' Nasıl Hesaplanıyor? — LÜTFEN OKU"):
        st.markdown(f"""
**Bu bir istatistiksel tahmin, fiyat hedefi veya öngörü DEĞİLDİR.** Hiçbir model
gelecekteki piyasa getirisini güvenilir şekilde tahmin edemez. "Görünüm" etiketi,
sadece iki basit bileşenin ortalamasından türetilen şeffaf bir **sezgisel senaryo
göstergesidir**:

1. **Momentum** — son 3 aylık gerçekleşen getirinin yönü (mevcut ayardaki eşik:
   ±%{esikler['momentum_esik']:.1f}). Bu, "trend devam eder mi" varsayımına dayanır —
   ki bu varsayımın kendisi de tartışmalıdır ve her zaman doğru çıkmaz.
2. **Katman 1 Bağlamı** — o varlık için ilgili rejim/değerleme/carry skorunun ortalaması
   (örn. BIST için "BIST Bağlamı" skoru, Altın için risk iştahı+DXY'nin ters skoru).

İkisinin ortalaması aynı 5 kademeli skalaya dönüştürülür: Yukarı Yönlü Eğilim →
Hafif Yukarı Eğilim → Yatay/Nötr → Hafif Aşağı Eğilim → Aşağı Yönlü Eğilim.

**Neden sayısal bir yüzde tahmini vermiyoruz?** Çünkü elimizdeki basit kural tabanlı
sistemin gerçek öngörü gücü istatistiksel olarak test edilmemiştir (backtest
yapılmamıştır). Sayısal bir rakam vermek, olduğundan çok daha fazla kesinlik
izlenimi yaratır. Etiket biçimindeki bu gösterim, bunun bir yönelim fikri olduğunu,
kesin bir sonuç olmadığını hatırlatmak için bilinçli bir tercihtir.

**Bu bir yatırım tavsiyesi değildir.** Kendi araştırmanı ve risk toleransını
dikkate alarak karar vermelisin.
        """)
        st.markdown("""
- **Risk profilleri farklı:** Hisse senetleri (BIST, ABD) günlük büyük dalgalanabilir;
  TL mevduatı ve altın görece daha az volatildir ama garantili değildir.
- **TL Mevduatı yaklaşık bir hesaplamadır:** Basit faiz mantığıyla (bileşik değil)
  hesaplanmıştır, gerçek mevduat ürünü koşulları (stopaj, vade, banka) farklılık gösterebilir.
- **USD/TRY satırı bir "varlık" değil, referans noktasıdır:** Sadece dolar cinsinden
  nakit tutmanın TL'ye kıyasla getirisini gösterir, karşılaştırma için taban çizgisi sayılabilir.
- **Geçmiş getiri gelecek performansın garantisi değildir.** Bu tablo bir karar destek
  aracıdır, yatırım tavsiyesi değildir.
        """)

    # ============================================================
    # KURUMSAL GÖRÜNÜM NOTLARI: Büyük kurumların ücretsiz yayınlanan
    # araştırma raporlarından derlenen hedefler (MANUEL GÜNCELLENİR)
    # ============================================================
    st.divider()
    st.subheader("📚 Kurumsal Görünüm Notları")
    st.caption(
        f"Büyük yatırım bankaları ve aracı kurumların ücretsiz yayınlanan araştırma "
        f"raporlarından derlenmiştir · **Derleme tarihi: {KURUMSAL_DERLEME_TARIHI}**. "
        "⚠️ Bu bölüm otomatik güncellenmez — deploy edilmiş uygulamanın canlı web "
        "erişimi yoktur. Güncel tutmak için Claude'a 'kurumsal görünüm verilerini "
        "güncelle' demen yeterli."
    )

    for varlik_adi, girdiler in KURUMSAL_GORUNUMLER.items():
        with st.expander(f"🏦 {varlik_adi} — {len(girdiler)} kurum takip ediliyor"):
            referans = MEVCUT_SEVIYE_REFERANS.get(varlik_adi, {})
            if referans:
                st.caption(
                    f"Referans seviye: {referans['deger']:,} {referans['birim']} "
                    f"({referans['tarih']}) — güncel canlı fiyat için Katman 1/3'e bak."
                )

            kurum_df = pd.DataFrame(girdiler)[["kurum", "tarih", "hedef", "gorus"]]
            kurum_df.columns = ["Kurum", "Rapor Tarihi", "Hedef", "Görüş"]
            st.dataframe(kurum_df, use_container_width=True, hide_index=True)

            # Basit konsensüs: bullish/nötr/bearish sayımı
            bullish = sum(1 for g in girdiler if "Bullish" in g["gorus"])
            bearish = sum(1 for g in girdiler if "Bearish" in g["gorus"])
            notr = len(girdiler) - bullish - bearish
            st.markdown(
                f"**Konsensüs yönü:** {bullish} Bullish · {notr} Nötr · {bearish} Bearish "
                f"({len(girdiler)} kurum arasında)"
            )

            # Kaynak linkleri
            st.markdown("**Kaynaklar:** " + " · ".join(
                f"[{g['kurum']}]({g['kaynak']})" for g in girdiler
            ))

    st.caption(GUVEN_AGIRLIGI_ACIKLAMA)

    with st.expander("⚠️ Kurumsal görünüm verilerini okurken dikkat edilmesi gerekenler"):
        st.markdown("""
- **Bu veriler kurumların KENDİ tahminleridir, gerçekleşmiş sonuç değildir.**
  Hedef fiyatlar sıkça revize edilir ve genellikle isabet oranı düşüktür — büyük
  bankaların bile geçmiş yıllardaki hedefleri gerçekleşenden belirgin şekilde
  sapmıştır.
- **Vade uyumsuzluğu:** Çoğu kurumsal hedef "yıl sonu" veya "12 aylık" ufka göre
  verilir, bizim Katman 2'deki 3-6 aylık ufkumuzla birebir örtüşmeyebilir —
  yön fikri olarak değerlendir, kesin zaman çizelgesi olarak değil.
- **Yayılım (dispersion) yüksekse dikkatli ol:** Örneğin altın için kurumlar
  arasında $4,800 ile $6,300 arasında geniş bir hedef aralığı var — bu, kurumların
  kendi aralarında da belirsizlik/anlaşmazlık içinde olduğunu gösterir.
- **Bu, kendi hesapladığımız 'Görünüm (3-6 Ay)' etiketinden ayrı bir kaynaktır**
  — matematiksel olarak birleştirilmemiştir, bilinçli olarak ayrı ayrı gösterilir
  ki hangi bilginin nereden geldiği net kalsın.
        """)

    st.divider()
    st.subheader("Diğer Varlıklar — Detaylı Tablo")
    st.dataframe(
        varlik_sonuclari,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Ticker": st.column_config.TextColumn("Ticker", help="Yahoo Finance sembol kodu."),
            "Hisse": st.column_config.TextColumn("Varlık", help="Varlığın açık adı."),
            f"Getiri (3 Ay)": st.column_config.NumberColumn(
                "Getiri (3 Ay)", help="Son 3 aylık (90 gün) yüzde getiri, USD bazlı.", format="%.2f%%"
            ),
            f"Getiri (6 Ay)": st.column_config.NumberColumn(
                "Getiri (6 Ay)", help="Son 6 aylık (180 gün) yüzde getiri, USD bazlı.", format="%.2f%%"
            ),
        },
    )

    st.caption(
        "Not: USD/TRY satırı, TL'nin dolar karşısındaki değer kaybını/kazancını gösterir. "
        "TL bazlı yatırımların USD getirisini yorumlarken bu satırı referans al. "
        "'ABD 10 Yıllık Tahvil Faizi' satırı ise tahvilin **toplam getirisi değil**, "
        "faiz (yield) seviyesindeki %değişimi gösterir — bu yüzden yukarıdaki ana "
        "karşılaştırma tablosuna dahil edilmemiştir."
    )

# ============================================================
# KATMAN 3: HİSSE SEÇİMİ
# ============================================================
with sekme3:
    st.subheader("Hisse Getirileri (3 ve 6 Aylık)")

    usd_try = usd_try_kuru_getir_cached()
    if usd_try:
        st.caption(f"Güncel USD/TRY kuru: {usd_try:.2f}")

    alt_sekme_bist, alt_sekme_abd = st.tabs(["🇹🇷 BIST", "🇺🇸 ABD"])

    with alt_sekme_bist:
        st.caption(
            "Getiriler USD bazlı hesaplanmıştır (her günün TL fiyatı, o günkü USD/TRY kuruna bölünerek). "
            "Karşılaştırma için TL bazlı getiri de parantez içinde ayrı sütunda gösterilmiştir."
        )
        bist_sonuclari = bist_listesi_usd_analiz_et_cached(BIST_HISSELER, VADE_GUN)

        # Sütun sırasını USD önce, TL sonra gelecek şekilde düzenle
        sutun_sirasi = ["Ticker", "Hisse"]
        for etiket in VADE_GUN:
            sutun_sirasi.append(f"Getiri ({etiket}, USD)")
            sutun_sirasi.append(f"Getiri ({etiket}, TL)")
        bist_sonuclari = bist_sonuclari[sutun_sirasi]

        st.dataframe(
            bist_sonuclari,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Ticker": st.column_config.TextColumn("Ticker", help="Yahoo Finance sembol kodu (.IS = BIST hissesi)."),
                "Hisse": st.column_config.TextColumn("Hisse", help="Şirketin açık adı."),
                "Getiri (3 Ay, USD)": st.column_config.NumberColumn(
                    "Getiri (3 Ay, USD)",
                    help="Son 3 aylık getiri, USD bazlı — her günün TL fiyatı o günkü USD/TRY kuruna bölünerek hesaplanır. Yatırımcının gerçek dolar bazlı kazancını yansıtır.",
                    format="%.2f%%",
                ),
                "Getiri (3 Ay, TL)": st.column_config.NumberColumn(
                    "Getiri (3 Ay, TL)",
                    help="Son 3 aylık getiri, TL bazlı — kur etkisi dahil değildir, sadece hissenin TL fiyat hareketini gösterir.",
                    format="%.2f%%",
                ),
                "Getiri (6 Ay, USD)": st.column_config.NumberColumn(
                    "Getiri (6 Ay, USD)", help="Son 6 aylık getiri, USD bazlı.", format="%.2f%%"
                ),
                "Getiri (6 Ay, TL)": st.column_config.NumberColumn(
                    "Getiri (6 Ay, TL)", help="Son 6 aylık getiri, TL bazlı (kur etkisi hariç).", format="%.2f%%"
                ),
            },
        )

    with alt_sekme_abd:
        abd_sonuclari = hisse_listesi_analiz_et_cached(ABD_HISSELER, VADE_GUN)
        st.dataframe(
            abd_sonuclari,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Ticker": st.column_config.TextColumn("Ticker", help="Yahoo Finance sembol kodu (NASDAQ/NYSE)."),
                "Hisse": st.column_config.TextColumn("Hisse", help="Şirketin açık adı."),
                "Getiri (3 Ay)": st.column_config.NumberColumn(
                    "Getiri (3 Ay)", help="Son 3 aylık (90 gün) yüzde getiri. ABD hisseleri zaten USD bazlı işlem gördüğü için ek kur dönüşümü gerekmez.", format="%.2f%%"
                ),
                "Getiri (6 Ay)": st.column_config.NumberColumn(
                    "Getiri (6 Ay)", help="Son 6 aylık (180 gün) yüzde getiri, USD bazlı.", format="%.2f%%"
                ),
            },
        )

st.divider()
st.caption(
    "⚠️ Bu panel yalnızca bilgi ve karar destek amaçlıdır, yatırım tavsiyesi niteliği taşımaz. "
    "Yatırım kararlarını kendi araştırman ve risk değerlendirmenle vermelisin."
)
