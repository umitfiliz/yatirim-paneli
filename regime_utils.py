"""
Katman 1'deki ham göstergeleri (VIX, USD/TRY, USD/CNY, Fed faiz yönü,
TCMB-Fed faiz farkı) yorumlayıp basit kural tabanlı bir "rejim özeti"
üreten fonksiyonlar. Bu özet Katman 2'ye bağlam olarak aktarılır.

Not: Bu yorumlar kesin öngörü değil, tarihsel genellemelere dayanan
basit sezgisel (heuristic) kurallardır. Yatırım tavsiyesi değildir.
"""

from data_utils import fiyat_gecmisi_getir, getiri_hesapla
from macro_utils import fred_veri_getir


def risk_istahi_degerlendir(vix_guncel: float | None, vix_degisim_7g: float | None) -> tuple[str, str]:
    """VIX seviyesine ve haftalık değişimine göre risk iştahını sınıflandırır."""
    if vix_guncel is None:
        return "Bilinmiyor", "VIX verisi alınamadı."

    if vix_guncel < 20:
        etiket = "Risk-On (İştahlı)"
    elif vix_guncel < 30:
        etiket = "Nötr"
    else:
        etiket = "Risk-Off (Kaçış)"

    yon_notu = ""
    if vix_degisim_7g is not None:
        if vix_degisim_7g > 5:
            yon_notu = " Son 7 günde korku/tedirginlik artıyor."
        elif vix_degisim_7g < -5:
            yon_notu = " Son 7 günde korku/tedirginlik azalıyor."

    return etiket, f"VIX {vix_guncel:.1f} seviyesinde.{yon_notu}"


def fed_faiz_yonu_degerlendir(fred_api_key: str) -> tuple[str, str]:
    """Fed faizinin son ~90 gündeki değişimine bakarak sıkılaşma/gevşeme yönünü belirler."""
    if not fred_api_key:
        return "Bilinmiyor", "FRED API key'i tanımlı değil."

    seri = fred_veri_getir("DFF", fred_api_key, gun_sayisi=100)
    if seri is None or len(seri) < 2:
        return "Bilinmiyor", "Yeterli veri alınamadı."

    fark = float(seri.iloc[-1] - seri.iloc[0])
    if fark > 0.1:
        return "Sıkılaşıyor", f"Son ~90 günde Fed faizi {fark:+.2f} puan değişti."
    elif fark < -0.1:
        return "Gevşiyor", f"Son ~90 günde Fed faizi {fark:+.2f} puan değişti."
    else:
        return "Sabit", "Son ~90 günde Fed faizinde belirgin bir yön değişikliği yok."


def sermaye_akisi_yonu_degerlendir(
    usdtry_degisim_30g: float | None, usdcny_degisim_30g: float | None
) -> tuple[str, str]:
    """
    USD/TRY ve USD/CNY'nin son 30 günlük değişimine bakarak gelişen piyasalara
    yönelik sermaye akışının genel yönü hakkında bir izlenim oluşturur.
    Dolar bu para birimleri karşısında güçleniyorsa (yüzde artış), bu genellikle
    gelişen piyasalardan sermaye çıkışıyla ilişkilendirilir.
    """
    degerler = [d for d in [usdtry_degisim_30g, usdcny_degisim_30g] if d is not None]
    if not degerler:
        return "Bilinmiyor", "Kur verisi alınamadı."

    ortalama = sum(degerler) / len(degerler)
    if ortalama > 2:
        return "Sermaye Çıkışı Sinyali", f"USD, TL/CNY karşısında ortalama %{ortalama:.1f} güçlendi (son 30 gün)."
    elif ortalama < -2:
        return "Sermaye Girişi Sinyali", f"USD, TL/CNY karşısında ortalama %{ortalama:.1f} zayıfladı (son 30 gün)."
    else:
        return "Nötr", f"USD/TL ve USD/CNY son 30 günde belirgin bir yön göstermiyor (ortalama %{ortalama:.1f})."


def carry_cazibesi_degerlendir(tcmb_faiz: float | None, fed_faiz: float | None) -> tuple[str | None, str]:
    """TCMB ve Fed faiz farkına bakarak TL varlıkların 'carry' (faiz farkı) cazibesini değerlendirir."""
    if tcmb_faiz is None or fed_faiz is None:
        return None, "Faiz verisi eksik olduğu için hesaplanamadı."

    fark = tcmb_faiz - fed_faiz
    if fark > 20:
        etiket = "Çok Yüksek"
    elif fark > 10:
        etiket = "Yüksek"
    else:
        etiket = "Orta/Düşük"

    return etiket, f"TCMB-Fed faiz farkı yaklaşık {fark:.1f} puan ({etiket.lower()} carry cazibesi)."


def genel_rejim_belirle(risk_etiket: str, sermaye_etiket: str) -> str:
    """Risk iştahı ve sermaye akışı etiketlerini birleştirip tek bir genel rejim adı üretir."""
    if risk_etiket.startswith("Risk-Off") and sermaye_etiket == "Sermaye Çıkışı Sinyali":
        return "Temkinli / Savunmacı"
    if risk_etiket.startswith("Risk-On") and sermaye_etiket == "Sermaye Girişi Sinyali":
        return "Destekleyici / Risk Alımına Uygun"
    if risk_etiket == "Nötr" and sermaye_etiket == "Nötr":
        return "Kararsız / Yatay"
    return "Karışık Sinyaller"


def rejim_ozeti_olustur(
    vix_guncel: float | None,
    vix_degisim_7g: float | None,
    usdtry_degisim_30g: float | None,
    usdcny_degisim_30g: float | None,
    tcmb_faiz: float | None,
    fed_faiz: float | None,
    fred_api_key: str,
) -> dict:
    """
    Tüm alt değerlendirmeleri birleştirip Katman 2'nin kullanabileceği
    tek bir rejim özeti sözlüğü üretir.
    """
    risk_etiket, risk_aciklama = risk_istahi_degerlendir(vix_guncel, vix_degisim_7g)
    fed_yon_etiket, fed_yon_aciklama = fed_faiz_yonu_degerlendir(fred_api_key)
    sermaye_etiket, sermaye_aciklama = sermaye_akisi_yonu_degerlendir(usdtry_degisim_30g, usdcny_degisim_30g)
    carry_etiket, carry_aciklama = carry_cazibesi_degerlendir(tcmb_faiz, fed_faiz)

    genel_rejim = genel_rejim_belirle(risk_etiket, sermaye_etiket)

    return {
        "genel_rejim": genel_rejim,
        "risk_istahi": {"etiket": risk_etiket, "aciklama": risk_aciklama},
        "fed_faiz_yonu": {"etiket": fed_yon_etiket, "aciklama": fed_yon_aciklama},
        "sermaye_akisi": {"etiket": sermaye_etiket, "aciklama": sermaye_aciklama},
        "carry_cazibesi": {"etiket": carry_etiket, "aciklama": carry_aciklama},
    }
