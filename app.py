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
from macro_utils import tum_politika_faizlerini_getir

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
    for i, (ticker, isim) in enumerate(MAKRO_GOSTERGELER.items()):
        veri = fiyat_gecmisi_getir_cached(ticker, gun_sayisi=30)
        with kolonlar[i % 3]:
            if not veri.empty:
                guncel = float(veri["Close"].dropna().iloc[-1])
                degisim = getiri_hesapla(veri, 7)  # haftalık değişim
                st.metric(
                    label=isim,
                    value=f"{guncel:,.2f}",
                    delta=f"{degisim}% (7 gün)" if degisim is not None else None,
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
# KATMAN 2: VARLIK SINIFI KIYASI
# ============================================================
with sekme2:
    st.subheader("Varlık Sınıfları Arası Getiri Kıyası (USD Bazlı)")

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
