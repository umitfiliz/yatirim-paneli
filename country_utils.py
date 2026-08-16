"""
Küresel makro göstergelerin yakalayamadığı, Türkiye ve ABD piyasalarına
özgü faktörleri çeken ve hesaplayan fonksiyonlar.

Örnek: Küresel risk iştahı yüksek olsa bile, BIST'in kendi değerleme
seviyesi pahalıysa veya TL'nin reel faizi negatifse, bu küresel resmi
yerel koşullarla dengelemek gerekir.
"""

import yfinance as yf
from data_utils import fiyat_gecmisi_getir, getiri_hesapla


def ortalama_fk_getir(hisse_sozlugu: dict) -> float | None:
    """
    Bir hisse sözlüğü ({ticker: isim}) için ortalama F/K (fiyat/kazanç)
    oranını hesaplar. yfinance'in trailingPE alanını kullanır.
    Veri gelmeyen veya negatif/sıfır olan hisseler hesaba katılmaz.
    """
    degerler = []
    for ticker in hisse_sozlugu:
        try:
            bilgi = yf.Ticker(ticker).info
            fk = bilgi.get("trailingPE")
            if fk is not None and fk > 0:
                degerler.append(fk)
        except Exception:
            continue
    if not degerler:
        return None
    return round(sum(degerler) / len(degerler), 2)


def dxy_getir() -> dict:
    """ABD Dolar Endeksi'nin (DXY) güncel değerini ve 30 günlük değişimini döner."""
    veri = fiyat_gecmisi_getir("DX-Y.NYB", gun_sayisi=60)
    if veri.empty:
        return {"guncel": None, "degisim_30g": None}
    guncel = float(veri["Close"].dropna().iloc[-1])
    degisim_30g = getiri_hesapla(veri, 30)
    return {"guncel": guncel, "degisim_30g": degisim_30g}


def abd_tahvil_getir() -> dict:
    """ABD 10 yıllık tahvil faizinin güncel değerini ve 30 günlük değişimini döner."""
    veri = fiyat_gecmisi_getir("^TNX", gun_sayisi=60)
    if veri.empty:
        return {"guncel": None, "degisim_30g": None}
    guncel = float(veri["Close"].dropna().iloc[-1])
    degisim_30g = getiri_hesapla(veri, 30)
    return {"guncel": guncel, "degisim_30g": degisim_30g}


def tr_reel_faiz_hesapla(tcmb_faiz: float | None, tufe_yillik: float | None) -> float | None:
    """TCMB politika faizinden yıllık TÜFE enflasyonunu çıkararak yaklaşık reel faizi hesaplar."""
    if tcmb_faiz is None or tufe_yillik is None:
        return None
    return round(tcmb_faiz - tufe_yillik, 2)
