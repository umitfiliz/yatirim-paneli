"""
BIST & ABD Yatırım Karar Destek Paneli
Katman 1: Makro Rejim | Katman 2: Varlık Sınıfı Kıyası | Katman 3: Hisse Seçimi

Çalıştırmak için: streamlit run app.py
"""

import streamlit as st
import pandas as pd

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
)
from data_utils import (
    fiyat_gecmisi_getir,
    getiri_hesapla,
    hisse_listesi_analiz_et,
    bist_listesi_usd_analiz_et,
    usd_try_kuru_getir,
)
from macro_utils import tum_politika_faizlerini_getir, tcmb_tufe_yillik_getir
from country_utils import ortalama_fk_getir, dxy_getir, abd_tahvil_getir, tr_reel_faiz_hesapla
from regime_utils import rejim_ozeti_olustur, tr_baglam_olustur, us_baglam_olustur

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
        )
        st.markdown(f"**ABD Bağlamı: {us_baglam['genel_baglam']}**")

    st.caption(
        "Not: F/K değerleme eşikleri basit sezgisel aralıklardır (kesin tarihsel "
        "ortalamaya dayanmaz), yorumlarken bunu göz önünde bulundur."
    )

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

    varlik_sonuclari = hisse_listesi_analiz_et_cached(DIGER_VARLIKLAR, VADE_GUN)
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
        "TL bazlı yatırımların USD getirisini yorumlarken bu satırı referans al."
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
