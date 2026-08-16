"""
Veri çekme ve getiri hesaplama yardımcı fonksiyonları.
Tüm fonksiyonlar yfinance üzerinden çalışır (API key gerektirmez).
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta


def fiyat_gecmisi_getir(ticker: str, gun_sayisi: int = 200) -> pd.DataFrame:
    """
    Belirtilen ticker için son N günlük kapanış fiyatlarını çeker.
    Streamlit'te tekrar tekrar aynı veriyi çekmemek için cache'lenmesi önerilir
    (app.py içinde @st.cache_data ile sarmalanacak).
    """
    baslangic = datetime.now() - timedelta(days=gun_sayisi + 10)
    veri = yf.download(ticker, start=baslangic, progress=False, auto_adjust=True)

    # yfinance'in yeni sürümleri tek hisse için bile çok katmanlı (MultiIndex)
    # sütun döndürebiliyor (örn. ('Close', 'AAPL')). Bunu düzleştiriyoruz ki
    # veri["Close"] her zaman tek boyutlu bir seri olsun.
    if isinstance(veri.columns, pd.MultiIndex):
        veri.columns = veri.columns.get_level_values(0)

    return veri


def _getiri_hesapla_seri(kapanislar: pd.Series, gun_sayisi: int) -> float | None:
    """
    Çekirdek getiri hesaplama mantığı — bir kapanış fiyatı serisi alır,
    belirtilen gün sayısı için yüzde getiri döner. Hem TL hem USD bazlı
    seriler için ortak kullanılır.
    """
    kapanislar = kapanislar.dropna()
    if len(kapanislar) < 2:
        return None

    guncel_fiyat = kapanislar.iloc[-1]

    hedef_tarih = kapanislar.index[-1] - timedelta(days=gun_sayisi)
    gecmis_veriler = kapanislar[kapanislar.index <= hedef_tarih]

    if gecmis_veriler.empty:
        # Yeterli geçmiş veri yoksa elimizdeki en eski fiyatı kullan
        eski_fiyat = kapanislar.iloc[0]
    else:
        eski_fiyat = gecmis_veriler.iloc[-1]

    if eski_fiyat == 0:
        return None

    getiri_yuzde = ((guncel_fiyat - eski_fiyat) / eski_fiyat) * 100
    return round(float(getiri_yuzde), 2)


def getiri_hesapla(fiyat_df: pd.DataFrame, gun_sayisi: int) -> float | None:
    """
    Belirtilen gün sayısı için yüzde getiri hesaplar.
    Örn: gun_sayisi=90 -> yaklaşık 3 aylık getiri.
    Yeterli veri yoksa None döner.
    """
    if fiyat_df.empty or len(fiyat_df) < 2:
        return None
    return _getiri_hesapla_seri(fiyat_df["Close"], gun_sayisi)


def usd_try_kuru_getir() -> float | None:
    """Güncel USD/TRY kurunu döner (TL bazlı getirileri USD'ye çevirmek için)."""
    try:
        veri = yf.download("TRY=X", period="5d", progress=False, auto_adjust=True)
        if isinstance(veri.columns, pd.MultiIndex):
            veri.columns = veri.columns.get_level_values(0)
        if veri.empty:
            return None
        return float(veri["Close"].dropna().iloc[-1])
    except Exception:
        return None


def ortalama_getiri(sonuc_df: pd.DataFrame, kolon: str) -> float | None:
    """
    Bir sonuç tablosundaki (örn. hisse_listesi_analiz_et çıktısı) belirtilen
    getiri sütununun ortalamasını hesaplar. Sütun yoksa veya tüm değerler
    eksikse None döner.
    """
    if kolon not in sonuc_df.columns:
        return None
    degerler = sonuc_df[kolon].dropna()
    if degerler.empty:
        return None
    return round(float(degerler.mean()), 2)
    """
    Bir hisse sözlüğü ({ticker: isim}) alır, her hisse için 3 ve 6 aylık
    getirileri hesaplayıp tek bir tablo (DataFrame) olarak döner.
    """
    sonuclar = []
    for ticker, isim in hisse_sozlugu.items():
        veri = fiyat_gecmisi_getir(ticker, gun_sayisi=200)
        satir = {"Ticker": ticker, "Hisse": isim}
        for etiket, gun in vade_gunleri.items():
            satir[f"Getiri ({etiket})"] = getiri_hesapla(veri, gun)
        sonuclar.append(satir)

    return pd.DataFrame(sonuclar)


def bist_listesi_usd_analiz_et(hisse_sozlugu: dict, vade_gunleri: dict) -> pd.DataFrame:
    """
    BIST hisseleri için hem TL hem USD bazlı getiriyi hesaplar.
    USD getirisi, her günün TL fiyatını o günkü USD/TRY kuruna bölerek
    (yani gerçek USD bazlı fiyat serisi oluşturarak) hesaplanır —
    sadece son kur ile düzeltme yapmaktan daha doğru bir yöntemdir.
    """
    try_verisi = fiyat_gecmisi_getir("TRY=X", gun_sayisi=200)
    try_kapanislari = try_verisi["Close"].dropna() if not try_verisi.empty else pd.Series(dtype=float)

    sonuclar = []
    for ticker, isim in hisse_sozlugu.items():
        veri = fiyat_gecmisi_getir(ticker, gun_sayisi=200)
        satir = {"Ticker": ticker, "Hisse": isim}

        if veri.empty or try_kapanislari.empty:
            for etiket in vade_gunleri:
                satir[f"Getiri ({etiket}, USD)"] = None
                satir[f"Getiri ({etiket}, TL)"] = None
            sonuclar.append(satir)
            continue

        tl_kapanislari = veri["Close"].dropna()

        # İki seriyi ortak tarihlere göre hizala (tatil günleri farklı olabiliyor)
        ortak_df = pd.DataFrame({
            "tl": tl_kapanislari,
            "kur": try_kapanislari,
        }).dropna()
        ortak_df["usd"] = ortak_df["tl"] / ortak_df["kur"]

        for etiket, gun in vade_gunleri.items():
            satir[f"Getiri ({etiket}, USD)"] = _getiri_hesapla_seri(ortak_df["usd"], gun)
            satir[f"Getiri ({etiket}, TL)"] = _getiri_hesapla_seri(tl_kapanislari, gun)

        sonuclar.append(satir)

    return pd.DataFrame(sonuclar)
