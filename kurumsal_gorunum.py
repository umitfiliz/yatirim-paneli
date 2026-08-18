"""
Büyük yatırım bankaları, varlık yönetim şirketleri ve yerel aracı kurumların
ÜCRETSİZ erişilebilir, kamuya açık araştırma/görünüm raporlarından derlenen
hedef fiyat ve görüş verileri.

ÖNEMLİ — BU DOSYA OTOMATİK GÜNCELLENMEZ:
Deploy edilmiş Streamlit uygulamasının canlı web erişimi yok, bu yüzden bu
veriler Claude ile yapılan bir sohbette web araması sonucunda derlenip elle
bu dosyaya işlenir. Güncellemek için: Claude'a "kurumsal görünüm verilerini
güncelle" de, yeni bir DERLEME_TARIHI ile bu dosyayı yeniden üretsin.

Her girişte kaynak URL'si var — iddiaları kendi gözünle doğrulayabilirsin.
"""

DERLEME_TARIHI = "19 Ağustos 2026"

# Her varlık sınıfı için mevcut piyasa seviyesi (derleme anında, referans amaçlı —
# Katman 1/3'teki canlı fiyatlarla küçük farklar olabilir, orası her zaman güncel)
MEVCUT_SEVIYE_REFERANS = {
    "Altın": {"deger": 4200, "birim": "USD/ons", "tarih": "Ağustos 2026 civarı (kaynaklar arası değişken)"},
    "ABD Hisseleri (S&P 500)": {"deger": 7757, "birim": "endeks puanı", "tarih": "~12 Ağustos 2026"},
    "BIST Hisseleri (BIST 100)": {"deger": 14150, "birim": "endeks puanı", "tarih": "17 Ağustos 2026"},
}

KURUMSAL_GORUNUMLER = {
    "Altın": [
        {"kurum": "J.P. Morgan Global Research", "tarih": "10 Haziran 2026", "hedef": "6,000 (2026 sonu)", "gorus": "Bullish", "kaynak": "https://www.jpmorgan.com/insights/global-research/commodities/gold-prices"},
        {"kurum": "Goldman Sachs Research", "tarih": "20 Haziran 2026", "hedef": "4,900 (2026 sonu, 5,400'den düşürüldü)", "gorus": "Bullish (temkinli)", "kaynak": "https://www.goldmansachs.com/insights/articles/s-and-p-500-forecast-to-climb-as-earnings-growth-powers-stocks-higher"},
        {"kurum": "UBS", "tarih": "Haziran 2026 (çeyreklik)", "hedef": "5,900 (2026 sonu)", "gorus": "Bullish", "kaynak": "https://capital.com/en-int/market-updates/gold-price-forecast-10-06-2026"},
        {"kurum": "Wells Fargo Investment Institute", "tarih": "Mart 2026", "hedef": "6,100-6,300", "gorus": "Bullish", "kaynak": "https://goldsilver.com/industry-news/article/gold-price-forecast-2026-2027-key-predictions-from-top-analysts/"},
        {"kurum": "Morgan Stanley", "tarih": "Mart 2026", "hedef": "4,800 (2026 sonu)", "gorus": "Nötr/Hafif Bullish", "kaynak": "https://goldsilver.com/industry-news/article/gold-price-forecast-2026-2027-key-predictions-from-top-analysts/"},
        {"kurum": "Bank of America", "tarih": "2026 (12 aylık)", "hedef": "6,000 (ekstrem senaryoda 8,000)", "gorus": "Bullish", "kaynak": "https://goldsilver.com/industry-news/article/gold-price-forecast-2026-2027-key-predictions-from-top-analysts/"},
    ],
    "ABD Hisseleri (S&P 500)": [
        {"kurum": "JPMorgan", "tarih": "~12 Ağustos 2026", "hedef": "8,000 (2026 sonu, 7,800'den yükseltildi)", "gorus": "Bullish", "kaynak": "https://finbold.com/wall-street-banking-giant-updates-sp-500-target-for-2026/"},
        {"kurum": "Goldman Sachs Research", "tarih": "26 Mayıs 2026", "hedef": "8,000 (2026 sonu, 7,600'den yükseltildi)", "gorus": "Bullish", "kaynak": "https://www.goldmansachs.com/insights/articles/s-and-p-500-forecast-to-climb-as-earnings-growth-powers-stocks-higher"},
        {"kurum": "Citigroup", "tarih": "~12 Ağustos 2026", "hedef": "8,100", "gorus": "Bullish", "kaynak": "https://finbold.com/wall-street-banking-giant-updates-sp-500-target-for-2026/"},
        {"kurum": "Yardeni Research", "tarih": "~12 Ağustos 2026", "hedef": "8,250", "gorus": "Bullish", "kaynak": "https://finbold.com/wall-street-banking-giant-updates-sp-500-target-for-2026/"},
    ],
    "BIST Hisseleri (BIST 100)": [
        {"kurum": "Gedik Yatırım", "tarih": "Ocak 2026 (12 aylık hedef — ESKİ, düşük ağırlıklı kabul et)", "hedef": "16,069", "gorus": "Bullish", "kaynak": "https://www.turkiyetoday.com/opinion/how-is-turkish-economy-entering-2026-with-early-signs-of-recovery-3212383"},
        {"kurum": "Tacirler Yatırım", "tarih": "Ocak 2026 (12 aylık hedef — ESKİ, düşük ağırlıklı kabul et)", "hedef": "15,200", "gorus": "Bullish", "kaynak": "https://www.turkiyetoday.com/opinion/how-is-turkish-economy-entering-2026-with-early-signs-of-recovery-3212383"},
    ],
}

# Bu görünümlerin dayandığı yayın tarihine göre kabaca güven ağırlığı.
# (Kullanıcının orijinal önerisindeki "rapor yaşı" mantığının basitleştirilmiş hali.)
GUVEN_AGIRLIGI_ACIKLAMA = """
0-30 gün: Yüksek ağırlık · 31-90 gün: Orta ağırlık · 91-180 gün: Düşük ağırlık ·
180+ gün: Sadece tarihsel referans. BIST 100 hedefleri Ocak 2026 tarihli olduğu
için (derleme anında ~7 ay eski) düşük ağırlıklı/tarihsel referans olarak
değerlendirilmelidir — ABD hisseleri ve altın verileri daha güncel (son 1-3 ay).
"""
