"""
Katman 1'deki ham göstergeleri (VIX, USD/TRY, USD/CNY, Fed faiz yönü,
TCMB-Fed faiz farkı) yorumlayıp basit kural tabanlı bir "rejim özeti"
üreten fonksiyonlar. Bu özet Katman 2'ye bağlam olarak aktarılır.
 
Not: Bu yorumlar kesin öngörü değil, tarihsel genellemelere dayanan
basit sezgisel (heuristic) kurallardır. Yatırım tavsiyesi değildir.
"""
 
from data_utils import fiyat_gecmisi_getir, getiri_hesapla
from macro_utils import fred_veri_getir
 
 
def risk_istahi_degerlendir(
    vix_guncel: float | None, vix_degisim_7g: float | None,
    risk_on_esik: float = 20.0, risk_off_esik: float = 30.0,
) -> tuple[str, str]:
    """VIX seviyesine ve haftalık değişimine göre risk iştahını sınıflandırır."""
    if vix_guncel is None:
        return "Bilinmiyor", "VIX verisi alınamadı."
 
    if vix_guncel < risk_on_esik:
        etiket = "Risk-On (İştahlı)"
    elif vix_guncel < risk_off_esik:
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
 
 
def fed_faiz_yonu_degerlendir(fred_api_key: str, esik: float = 0.1) -> tuple[str, str]:
    """Fed faizinin son ~90 gündeki değişimine bakarak sıkılaşma/gevşeme yönünü belirler."""
    if not fred_api_key:
        return "Bilinmiyor", "FRED API key'i tanımlı değil."
 
    seri = fred_veri_getir("DFF", fred_api_key, gun_sayisi=100)
    if seri is None or len(seri) < 2:
        return "Bilinmiyor", "Yeterli veri alınamadı."
 
    fark = float(seri.iloc[-1] - seri.iloc[0])
    if fark > esik:
        return "Sıkılaşıyor", f"Son ~90 günde Fed faizi {fark:+.2f} puan değişti."
    elif fark < -esik:
        return "Gevşiyor", f"Son ~90 günde Fed faizi {fark:+.2f} puan değişti."
    else:
        return "Sabit", "Son ~90 günde Fed faizinde belirgin bir yön değişikliği yok."
 
 
def sermaye_akisi_yonu_degerlendir(
    usdtry_degisim_30g: float | None, usdcny_degisim_30g: float | None, esik: float = 2.0
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
    if ortalama > esik:
        return "Sermaye Çıkışı Sinyali", f"USD, TL/CNY karşısında ortalama %{ortalama:.1f} güçlendi (son 30 gün)."
    elif ortalama < -esik:
        return "Sermaye Girişi Sinyali", f"USD, TL/CNY karşısında ortalama %{ortalama:.1f} zayıfladı (son 30 gün)."
    else:
        return "Nötr", f"USD/TL ve USD/CNY son 30 günde belirgin bir yön göstermiyor (ortalama %{ortalama:.1f})."
 
 
def carry_cazibesi_degerlendir(
    tcmb_faiz: float | None, fed_faiz: float | None,
    yuksek_esik: float = 10.0, cok_yuksek_esik: float = 20.0,
) -> tuple[str | None, str]:
    """TCMB ve Fed faiz farkına bakarak TL varlıkların 'carry' (faiz farkı) cazibesini değerlendirir."""
    if tcmb_faiz is None or fed_faiz is None:
        return None, "Faiz verisi eksik olduğu için hesaplanamadı."
 
    fark = tcmb_faiz - fed_faiz
    if fark > cok_yuksek_esik:
        etiket = "Çok Yüksek"
    elif fark > yuksek_esik:
        etiket = "Yüksek"
    else:
        etiket = "Orta/Düşük"
 
    return etiket, f"TCMB-Fed faiz farkı yaklaşık {fark:.1f} puan ({etiket.lower()} carry cazibesi)."
 
 
def tr_reel_faiz_degerlendir(reel_faiz: float | None) -> tuple[str, str]:
    """TCMB reel faizinin (politika faizi - enflasyon) seviyesini değerlendirir."""
    if reel_faiz is None:
        return "Bilinmiyor", "Veri eksik (TÜFE için EVDS API key'i gerekli)."
    if reel_faiz >= 5:
        etiket = "Güçlü Pozitif"
    elif reel_faiz >= 0:
        etiket = "Hafif Pozitif"
    else:
        etiket = "Negatif"
    return etiket, f"Yaklaşık reel faiz: %{reel_faiz:.1f} (TCMB faizi - yıllık TÜFE enflasyonu)."
 
 
def degerleme_degerlendir(ortalama_fk: float | None, ucuz_esik: float, pahali_esik: float, piyasa_adi: str) -> tuple[str, str]:
    """
    Ortalama F/K oranına göre bir hisse grubunun değerleme seviyesini
    kabaca sınıflandırır. Eşikler basit bir sezgiseldir, kesin bir
    tarihsel ortalamaya dayanmaz — yorumlarken bunu göz önünde bulundur.
    """
    if ortalama_fk is None:
        return "Bilinmiyor", "F/K verisi alınamadı."
    if ortalama_fk < ucuz_esik:
        etiket = "Ucuz/Makul"
    elif ortalama_fk <= pahali_esik:
        etiket = "Makul"
    else:
        etiket = "Pahalı"
    return etiket, f"İzlenen {piyasa_adi} hisselerinin ortalama F/K'sı ~{ortalama_fk:.1f}."
 
 
def dxy_etkisi_degerlendir(dxy_degisim_30g: float | None, esik: float = 2.0) -> tuple[str, str]:
    """Dolar Endeksi'nin (DXY) son 30 günlük değişiminin TL/EM üzerindeki baskısını değerlendirir."""
    if dxy_degisim_30g is None:
        return "Bilinmiyor", "DXY verisi alınamadı."
    if dxy_degisim_30g > esik:
        etiket = "TL/EM İçin Baskı"
    elif dxy_degisim_30g < -esik:
        etiket = "TL/EM İçin Destek"
    else:
        etiket = "Nötr"
    return etiket, f"DXY son 30 günde %{dxy_degisim_30g:.1f} değişti."
 
 
def abd_tahvil_yonu_degerlendir(tnx_degisim_30g: float | None, esik: float = 3.0) -> tuple[str, str]:
    """ABD 10 yıllık tahvil faizinin trendinin hisse değerlemeleri üzerindeki baskısını değerlendirir."""
    if tnx_degisim_30g is None:
        return "Bilinmiyor", "Tahvil faizi verisi alınamadı."
    if tnx_degisim_30g > esik:
        etiket = "Yükseliyor (Değerleme Baskısı)"
    elif tnx_degisim_30g < -esik:
        etiket = "Düşüyor (Değerleme Desteği)"
    else:
        etiket = "Stabil"
    return etiket, f"ABD 10 yıllık tahvil faizi son 30 günde %{tnx_degisim_30g:.1f} değişti."
 
 
def _ortalama_skor_ve_etiket(dokum: list[dict]) -> tuple[str, float | None]:
    """Bir bileşen dökümünden ortalama skoru ve buna karşılık gelen etiketi üretir."""
    gecerli_skorlar = [d["skor"] for d in dokum if d["skor"] is not None]
    if not gecerli_skorlar:
        return "Bilinmiyor (yeterli veri yok)", None
 
    ortalama = sum(gecerli_skorlar) / len(gecerli_skorlar)
    if ortalama >= 0.6:
        etiket = "Destekleyici"
    elif ortalama >= 0.2:
        etiket = "Ilımlı Destekleyici"
    elif ortalama > -0.2:
        etiket = "Nötr / Yatay"
    elif ortalama > -0.6:
        etiket = "Ilımlı Temkinli"
    else:
        etiket = "Temkinli / Savunmacı"
 
    if len(gecerli_skorlar) >= 2 and (max(gecerli_skorlar) - min(gecerli_skorlar) >= 2):
        etiket += " — bileşenler arasında çelişki var"
 
    return etiket, ortalama
 
 
def tr_baglam_olustur(
    reel_faiz: float | None,
    bist_ortalama_fk: float | None,
    dxy_degisim_30g: float | None,
    carry_etiket: str | None,
    esikler: dict | None = None,
) -> dict:
    """Türkiye'ye özgü faktörleri birleştirip BIST için ayrı bir bağlam özeti üretir."""
    e = esikler or {}
    reel_faiz_etiket, reel_faiz_aciklama = tr_reel_faiz_degerlendir(reel_faiz)
    bist_deger_etiket, bist_deger_aciklama = degerleme_degerlendir(
        bist_ortalama_fk,
        ucuz_esik=e.get("bist_fk_ucuz", 8.0),
        pahali_esik=e.get("bist_fk_pahali", 14.0),
        piyasa_adi="BIST",
    )
    dxy_etiket, dxy_aciklama = dxy_etkisi_degerlendir(dxy_degisim_30g, esik=e.get("dxy_esik", 2.0))
 
    haritalar = {
        "reel_faiz": {"Güçlü Pozitif": 1, "Hafif Pozitif": 0, "Negatif": -1},
        "degerleme": {"Ucuz/Makul": 1, "Makul": 0, "Pahalı": -1},
        "dxy": {"TL/EM İçin Destek": 1, "Nötr": 0, "TL/EM İçin Baskı": -1},
        "carry": {"Çok Yüksek": 1, "Yüksek": 1, "Orta/Düşük": 0},
    }
 
    dokum = [
        {"bilesen": "TL Reel Faizi", "etiket": reel_faiz_etiket, "skor": haritalar["reel_faiz"].get(reel_faiz_etiket)},
        {"bilesen": "BIST Değerlemesi (Ort. F/K)", "etiket": bist_deger_etiket, "skor": haritalar["degerleme"].get(bist_deger_etiket)},
        {"bilesen": "Dolar Endeksi (DXY) Etkisi", "etiket": dxy_etiket, "skor": haritalar["dxy"].get(dxy_etiket)},
        {"bilesen": "TL Carry Cazibesi", "etiket": carry_etiket or "Bilinmiyor", "skor": haritalar["carry"].get(carry_etiket)},
    ]
 
    genel_baglam, ortalama_skor = _ortalama_skor_ve_etiket(dokum)
 
    return {
        "genel_baglam": genel_baglam,
        "ortalama_skor": ortalama_skor,
        "dokum": dokum,
        "reel_faiz": {"etiket": reel_faiz_etiket, "aciklama": reel_faiz_aciklama},
        "degerleme": {"etiket": bist_deger_etiket, "aciklama": bist_deger_aciklama},
        "dxy": {"etiket": dxy_etiket, "aciklama": dxy_aciklama},
    }
 
 
def us_baglam_olustur(
    fed_yon_etiket: str,
    abd_ortalama_fk: float | None,
    tnx_degisim_30g: float | None,
    esikler: dict | None = None,
) -> dict:
    """ABD'ye özgü faktörleri birleştirip ABD hisseleri için ayrı bir bağlam özeti üretir."""
    e = esikler or {}
    abd_deger_etiket, abd_deger_aciklama = degerleme_degerlendir(
        abd_ortalama_fk,
        ucuz_esik=e.get("abd_fk_ucuz", 20.0),
        pahali_esik=e.get("abd_fk_pahali", 30.0),
        piyasa_adi="ABD",
    )
    tahvil_etiket, tahvil_aciklama = abd_tahvil_yonu_degerlendir(tnx_degisim_30g, esik=e.get("tahvil_esik", 3.0))
 
    haritalar = {
        "fed": {"Gevşiyor": 1, "Sabit": 0, "Sıkılaşıyor": -1},
        "degerleme": {"Ucuz/Makul": 1, "Makul": 0, "Pahalı": -1},
        "tahvil": {"Düşüyor (Değerleme Desteği)": 1, "Stabil": 0, "Yükseliyor (Değerleme Baskısı)": -1},
    }
 
    dokum = [
        {"bilesen": "Fed Faiz Yönü", "etiket": fed_yon_etiket, "skor": haritalar["fed"].get(fed_yon_etiket)},
        {"bilesen": "ABD Hisseleri Değerlemesi (Ort. F/K)", "etiket": abd_deger_etiket, "skor": haritalar["degerleme"].get(abd_deger_etiket)},
        {"bilesen": "10 Yıllık Tahvil Faizi Trendi", "etiket": tahvil_etiket, "skor": haritalar["tahvil"].get(tahvil_etiket)},
    ]
 
    genel_baglam, ortalama_skor = _ortalama_skor_ve_etiket(dokum)
 
    return {
        "genel_baglam": genel_baglam,
        "ortalama_skor": ortalama_skor,
        "dokum": dokum,
        "degerleme": {"etiket": abd_deger_etiket, "aciklama": abd_deger_aciklama},
        "tahvil": {"etiket": tahvil_etiket, "aciklama": tahvil_aciklama},
    }
 
 
def altin_baglam_olustur(risk_istahi_etiket: str, dxy_etiket: str) -> dict:
    """
    Altın için basit bir bağlam üretir. Altın tipik olarak risk-off dönemlerde
    ve dolar zayıfken (DXY düşerken) daha cazip hale gelir — bu yüzden risk
    iştahı ve DXY etkisinin işareti burada TERSİNE çevrilerek kullanılır.
    """
    haritalar = {
        "risk_ters": {"Risk-Off (Kaçış)": 1, "Nötr": 0, "Risk-On (İştahlı)": -1},
        "dxy_ters": {"TL/EM İçin Destek": 1, "Nötr": 0, "TL/EM İçin Baskı": -1},
    }
    risk_skor = None
    for anahtar, skor in haritalar["risk_ters"].items():
        if risk_istahi_etiket.startswith(anahtar.split(" (")[0]):
            risk_skor = skor
            break
 
    dokum = [
        {"bilesen": "Risk İştahının Altına Etkisi", "etiket": risk_istahi_etiket, "skor": risk_skor},
        {"bilesen": "Dolar Endeksinin (DXY) Altına Etkisi", "etiket": dxy_etiket, "skor": haritalar["dxy_ters"].get(dxy_etiket)},
    ]
    genel_baglam, ortalama_skor = _ortalama_skor_ve_etiket(dokum)
    return {"genel_baglam": genel_baglam, "ortalama_skor": ortalama_skor, "dokum": dokum}
 
 
def mevduat_baglam_olustur(carry_etiket: str | None) -> dict:
    """TL mevduatı için bağlam — esas olarak carry cazibesine dayanır."""
    haritalar = {"Çok Yüksek": 1, "Yüksek": 1, "Orta/Düşük": 0}
    dokum = [
        {"bilesen": "TL Carry Cazibesi", "etiket": carry_etiket or "Bilinmiyor", "skor": haritalar.get(carry_etiket)},
    ]
    genel_baglam, ortalama_skor = _ortalama_skor_ve_etiket(dokum)
    return {"genel_baglam": genel_baglam, "ortalama_skor": ortalama_skor, "dokum": dokum}
 
 
def usdtry_baglam_olustur(sermaye_etiket: str) -> dict:
    """
    USD/TRY referans satırı için bağlam. Sermaye çıkışı sinyali USD/TRY'nin
    yükselmesini (dolar güçlenmesini) destekler, bu yüzden işaret buna göredir
    (sermaye çıkışı = bu satırın 'getirisi' için pozitif).
    """
    haritalar = {"Sermaye Çıkışı Sinyali": 1, "Nötr": 0, "Sermaye Girişi Sinyali": -1}
    dokum = [
        {"bilesen": "TL/EM Sermaye Akışı Yönü", "etiket": sermaye_etiket, "skor": haritalar.get(sermaye_etiket)},
    ]
    genel_baglam, ortalama_skor = _ortalama_skor_ve_etiket(dokum)
    return {"genel_baglam": genel_baglam, "ortalama_skor": ortalama_skor, "dokum": dokum}
 
 
def momentum_skoru_hesapla(getiri_3ay: float | None, esik: float = 2.0) -> int | None:
    """Son 3 aylık getirinin yönüne göre basit bir momentum skoru (-1/0/+1) üretir."""
    if getiri_3ay is None:
        return None
    if getiri_3ay > esik:
        return 1
    elif getiri_3ay < -esik:
        return -1
    return 0
 
 
def gorunum_etiketle(skor: float | None) -> str:
    """Bir bileşik skoru (momentum + bağlam ortalaması) 3-6 aylık yönelim etiketine çevirir."""
    if skor is None:
        return "Bilinmiyor (yeterli veri yok)"
    if skor >= 0.6:
        return "Yukarı Yönlü Eğilim"
    elif skor >= 0.2:
        return "Hafif Yukarı Eğilim"
    elif skor > -0.2:
        return "Yatay / Nötr"
    elif skor > -0.6:
        return "Hafif Aşağı Eğilim"
    else:
        return "Aşağı Yönlü Eğilim"
 
 
def gorunum_olustur(momentum_skor: int | None, baglam_skor: float | None) -> tuple[str, float | None]:
    """
    Momentum (son 3 ay yönü) ve ilgili bağlam skorunu (rejim/değerleme/carry vb.)
    birleştirip 3-6 aylık bir yönelim etiketi üretir. Bu KESİN BİR TAHMİN DEĞİLDİR —
    basit, şeffaf bir sezgisel senaryodur.
    """
    degerler = [d for d in [momentum_skor, baglam_skor] if d is not None]
    if not degerler:
        return "Bilinmiyor (yeterli veri yok)", None
    ortalama = sum(degerler) / len(degerler)
    return gorunum_etiketle(ortalama), ortalama
 
 
def genel_rejim_belirle(risk_etiket: str, sermaye_etiket: str, fed_yon_etiket: str) -> tuple[str, list[dict]]:
    """
    Risk iştahı, sermaye akışı ve Fed faiz yönü etiketlerini bir puanlama
    sistemiyle birleştirir. Basit "ikili kural" yerine her bileşene -1/0/+1
    puan vererek ortalamasını alır — bu, sonucun daha kademeli (siyah-beyaz
    olmayan) ve şeffaf olmasını sağlar. Ayrıca hangi bileşenin hangi yöne
    çektiğini gösteren bir döküm (breakdown) döner.
    """
    haritalar = {
        "risk": {"Risk-On (İştahlı)": 1, "Nötr": 0, "Risk-Off (Kaçış)": -1},
        "sermaye": {"Sermaye Girişi Sinyali": 1, "Nötr": 0, "Sermaye Çıkışı Sinyali": -1},
        "fed": {"Gevşiyor": 1, "Sabit": 0, "Sıkılaşıyor": -1},
    }
 
    dokum = [
        {"bilesen": "Risk İştahı (VIX)", "etiket": risk_etiket, "skor": haritalar["risk"].get(risk_etiket)},
        {"bilesen": "TL/EM Sermaye Akışı", "etiket": sermaye_etiket, "skor": haritalar["sermaye"].get(sermaye_etiket)},
        {"bilesen": "Fed Faiz Yönü", "etiket": fed_yon_etiket, "skor": haritalar["fed"].get(fed_yon_etiket)},
    ]
 
    gecerli_skorlar = [d["skor"] for d in dokum if d["skor"] is not None]
    if not gecerli_skorlar:
        return "Bilinmiyor (yeterli veri yok)", dokum
 
    ortalama = sum(gecerli_skorlar) / len(gecerli_skorlar)
 
    if ortalama >= 0.6:
        etiket = "Destekleyici"
    elif ortalama >= 0.2:
        etiket = "Ilımlı Destekleyici"
    elif ortalama > -0.2:
        etiket = "Nötr / Yatay"
    elif ortalama > -0.6:
        etiket = "Ilımlı Temkinli"
    else:
        etiket = "Temkinli / Savunmacı"
 
    # Netlik kontrolü: bileşenler birbirine tamamen zıt yöndeyse bunu belirt
    # (örn. risk iştahı olumluyken sermaye TL'den çıkıyor gibi çelişkili bir durum)
    if len(gecerli_skorlar) >= 2 and (max(gecerli_skorlar) - min(gecerli_skorlar) >= 2):
        etiket += " — bileşenler arasında çelişki var, aşağıdaki döküme bak"
 
    return etiket, dokum
 
 
def rejim_ozeti_olustur(
    vix_guncel: float | None,
    vix_degisim_7g: float | None,
    usdtry_degisim_30g: float | None,
    usdcny_degisim_30g: float | None,
    tcmb_faiz: float | None,
    fed_faiz: float | None,
    fred_api_key: str,
    esikler: dict | None = None,
) -> dict:
    """
    Tüm alt değerlendirmeleri birleştirip Katman 2'nin kullanabileceği
    tek bir rejim özeti sözlüğü üretir.
    """
    e = esikler or {}
    risk_etiket, risk_aciklama = risk_istahi_degerlendir(
        vix_guncel, vix_degisim_7g,
        risk_on_esik=e.get("vix_risk_on", 20.0), risk_off_esik=e.get("vix_risk_off", 30.0),
    )
    fed_yon_etiket, fed_yon_aciklama = fed_faiz_yonu_degerlendir(fred_api_key, esik=e.get("fed_yon_esik", 0.1))
    sermaye_etiket, sermaye_aciklama = sermaye_akisi_yonu_degerlendir(
        usdtry_degisim_30g, usdcny_degisim_30g, esik=e.get("sermaye_esik", 2.0)
    )
    carry_etiket, carry_aciklama = carry_cazibesi_degerlendir(
        tcmb_faiz, fed_faiz,
        yuksek_esik=e.get("carry_yuksek", 10.0), cok_yuksek_esik=e.get("carry_cok_yuksek", 20.0),
    )
 
    genel_rejim, dokum = genel_rejim_belirle(risk_etiket, sermaye_etiket, fed_yon_etiket)
 
    return {
        "genel_rejim": genel_rejim,
        "dokum": dokum,
        "risk_istahi": {"etiket": risk_etiket, "aciklama": risk_aciklama},
        "fed_faiz_yonu": {"etiket": fed_yon_etiket, "aciklama": fed_yon_aciklama},
        "sermaye_akisi": {"etiket": sermaye_etiket, "aciklama": sermaye_aciklama},
        "carry_cazibesi": {"etiket": carry_etiket, "aciklama": carry_aciklama},
    }