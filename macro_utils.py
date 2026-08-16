"""
FRED (ABD/ECB) ve TCMB (borsapy üzerinden) API entegrasyonu için
politika faizi verilerini otomatik çeken fonksiyonlar.

FRED key'i Streamlit secrets üzerinden okunur (bkz. .streamlit/secrets.toml.example).
Key'leri asla doğrudan koda yazma — GitHub'a yüklenince herkese görünür olur.

TCMB politika faizi için 'borsapy' kütüphanesi kullanılıyor. Sebep: TCMB, EVDS
web servisini 2025 sonunda evds2 -> evds3'e taşırken alttaki API yapısını da
kökten değiştirdi (artık resmi olarak belgelenmemiş bir backend kullanıyor).
borsapy bu yeni backend'i sarmalıyor ve politika faizi için API key bile
gerektirmiyor (halka açık sayfadan okuyor).

Not: borsapy "yalnızca kişisel kullanım ve eğitim amaçlıdır" lisansı ile
dağıtılıyor - bu proje o kapsama uyuyor.
"""

import requests
import pandas as pd
from datetime import datetime, timedelta


# --- FRED (Federal Reserve Economic Data) ---
# Fed ve ECB için kullanılan seri kodları (doğrulanmış, güncel):
FRED_SERI_KODLARI = {
    "Fed Faiz Oranı (%)": "DFF",       # Effective Federal Funds Rate, günlük
    "ECB Faiz Oranı (%)": "ECBDFR",    # ECB Deposit Facility Rate, günlük
    "PBOC Faiz Oranı (%)": "IRSTCB01CNM156N",  # OECD - Çin, aylık, gecikmeli güncellenebilir
    "BOJ Faiz Oranı (%)": "IRSTCB01JPM156N",   # OECD - Japonya, aylık, gecikmeli güncellenebilir
}


def fred_veri_getir(series_id: str, api_key: str, gun_sayisi: int = 400) -> pd.Series | None:
    """
    FRED API'den belirtilen seri için son N günlük veriyi çeker.
    Başarısız olursa None döner (uygulamanın çökmemesi için).
    """
    baslangic = (datetime.now() - timedelta(days=gun_sayisi)).strftime("%Y-%m-%d")
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        "observation_start": baslangic,
    }
    try:
        yanit = requests.get(url, params=params, timeout=10)
        yanit.raise_for_status()
        veri = yanit.json()
        gozlemler = veri.get("observations", [])
        if not gozlemler:
            return None

        seri = pd.Series(
            {
                pd.to_datetime(g["date"]): float(g["value"])
                for g in gozlemler
                if g["value"] != "."  # FRED eksik veriyi "." ile işaretler
            }
        )
        return seri.sort_index() if not seri.empty else None
    except Exception:
        return None


# --- TCMB (borsapy üzerinden) ---
def tcmb_politika_faizi_getir() -> float | None:
    """
    TCMB'nin güncel politika faizini (1 haftalık repo faiz oranı) döner.
    borsapy kütüphanesi bunu TCMB'nin kendi sayfasından okuyor, API key
    gerektirmiyor. Başarısız olursa veya sonuç mantıksız görünüyorsa None döner.

    Not: borsapy üçüncü parti bir kütüphane ve TCMB'nin sayfa yapısı
    değişirse ayrıştırma hatası yapabilir (örn. "%37" değerini "%7" olarak
    okuma gibi). Bu yüzden sonucu, Türkiye'nin son birkaç yıldaki
    politika faizi aralığına göre makul olup olmadığını kontrol ediyoruz.
    Bu aralık zamanla güncellenmesi gereken bir sağlık kontrolüdür, kesin
    bir doğrulama değildir.
    """
    try:
        import borsapy as bp
        deger = bp.TCMB().policy_rate
        if deger is None:
            return None
        deger = round(float(deger), 2)

        # Mantıksızlık kontrolü: TCMB faizi son yıllarda %15-%60 aralığında
        # seyretti. Bu aralığın dışında bir değer muhtemelen ayrıştırma
        # hatasıdır (örn. "%37" -> "%7" gibi basamak kaybı).
        if not (15 <= deger <= 60):
            return None

        return deger
    except Exception:
        return None


def tcmb_tufe_yillik_getir(evds_api_key: str) -> float | None:
    """
    TCMB'nin TÜFE (enflasyon) verisinin yıllık yüzde değişimini döner.
    Bu, borsapy'nin EVDS sarmalayıcısını kullanır ve bir EVDS API key'i
    gerektirir (ücretsiz, evds3.tcmb.gov.tr'den alınır).
    Başarısız olursa None döner.
    """
    try:
        import borsapy as bp
        bp.set_evds_key(evds_api_key)
        seri = bp.evds_series("TP.FG.J0", period="3y", formula="yoy_pct")
        if seri is None or seri.empty:
            return None
        son_deger = seri.iloc[-1]
        # Sütun bir DataFrame olabilir, tek sütun ise değeri çıkar
        if hasattr(son_deger, "iloc"):
            son_deger = son_deger.iloc[0]
        return round(float(son_deger), 2)
    except Exception:
        return None


def tum_politika_faizlerini_getir(fred_api_key: str, evds_api_key: str = "") -> dict:
    """
    Tüm merkez bankası faizlerini (Fed, ECB, PBOC, BOJ, TCMB) tek seferde
    çeker ve en güncel değerleriyle birlikte döner.
    Bir kaynak başarısız olursa o gösterge için None döner, diğerleri etkilenmez.
    """
    sonuclar = {}

    # PBOC ve BOJ, OECD kaynaklı aylık serilerden geliyor ve bazen 1 yıla kadar
    # gecikmeli güncellenebiliyor. Bu yüzden bunlara daha geniş bir arama
    # penceresi (900 gün) veriyoruz, diğerlerine (günlük seriler) 400 gün yeterli.
    genis_pencere_gerektirenler = {"PBOC Faiz Oranı (%)", "BOJ Faiz Oranı (%)"}

    for isim, kod in FRED_SERI_KODLARI.items():
        gun_sayisi = 900 if isim in genis_pencere_gerektirenler else 400
        seri = fred_veri_getir(kod, fred_api_key, gun_sayisi=gun_sayisi)
        sonuclar[isim] = round(float(seri.iloc[-1]), 2) if seri is not None else None

    # TCMB politika faizi - borsapy üzerinden, key gerekmez
    sonuclar["TCMB Faiz Oranı (%)"] = tcmb_politika_faizi_getir()

    return sonuclar
