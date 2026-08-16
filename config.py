"""
Proje konfigürasyonu: takip edilen hisseler, varlıklar ve makro göstergeler.
Listeleri buradan güncelleyebilirsin — kodun geri kalanına dokunmana gerek yok.
"""

# --- KATMAN 3: Hisse listeleri ---
# BIST hisseleri Yahoo Finance formatında ".IS" son eki ile
BIST_HISSELER = {
    "THYAO.IS": "Türk Hava Yolları",
    "ASELS.IS": "Aselsan",
    "SASA.IS": "Sasa Polyester",
    "KCHOL.IS": "Koç Holding",
    "EREGL.IS": "Ereğli Demir Çelik",
    "TUPRS.IS": "Tüpraş",
}

ABD_HISSELER = {
    "AAPL": "Apple",
    "MSFT": "Microsoft",
    "NVDA": "Nvidia",
    "AMZN": "Amazon",
    "GOOGL": "Alphabet",
    "TSLA": "Tesla",
}

# --- KATMAN 2: Kıyaslanacak diğer varlıklar (Yahoo Finance ticker'ları) ---
DIGER_VARLIKLAR = {
    "GC=F": "Altın (Ons/USD)",
    "TRY=X": "USD/TRY",
    "^TNX": "ABD 10 Yıllık Tahvil Faizi",
}

# --- KATMAN 1: Makro rejim göstergeleri (yfinance üzerinden çekilebilenler) ---
MAKRO_GOSTERGELER = {
    "^VIX": "VIX (Risk İştahı)",
    "TRY=X": "USD/TRY",
    "EURUSD=X": "EUR/USD",
    "JPY=X": "USD/JPY",
    "CNY=X": "USD/CNY",
    "BZ=F": "Brent Petrol",
    "EEM": "MSCI EM Proxy (Gelişen Piyasalar)",
}

# Not: Fed/ECB/PBOC/BOJ/TCMB politika faizleri yfinance'te yok.
# Bunlar için FRED (ABD/ECB) ve TCMB EVDS API'lerini ayrı bir modülde
# entegre edeceğiz (bir sonraki adım). Şimdilik bu değerleri manuel
# güncelleyebilmen için aşağıda yer tutucu bırakıyorum.
POLITIKA_FAIZLERI_MANUEL = {
    "Fed Faiz Oranı (%)": 4.25,      # En son FOMC kararına göre güncelle
    "TCMB Faiz Oranı (%)": 37.0,     # En son PPK kararına göre güncelle (16 Ağustos 2026 itibarıyla doğrulandı)
    "ECB Faiz Oranı (%)": 2.15,
    "PBOC Faiz Oranı (%)": 3.10,
    "BOJ Faiz Oranı (%)": 0.50,
}

# Getiri hesaplamalarında kullanılacak vade (gün)
VADE_GUN = {
    "3 Ay": 90,
    "6 Ay": 180,
}

# --- Gösterge açıklamaları ve yorumlama rehberi ---
# Her gösterge için: (1) ne olduğu, (2) yüksek/düşük değerin ne anlama geldiği.
# st.metric'in "help" parametresinde tooltip olarak gösterilir.
MAKRO_GOSTERGE_BILGI = {
    "VIX (Risk İştahı)": (
        "VIX (Volatilite Endeksi): S&P 500 opsiyonlarından hesaplanan, piyasanın "
        "beklediği 30 günlük oynaklığı gösteren endeks — 'korku endeksi' olarak da bilinir.\n\n"
        "**Yorumlama:** 20'nin altı = düşük risk algısı, yatırımcılar risk almaya istekli "
        "('risk-on'). 20-30 arası = orta düzey belirsizlik. 30 üzeri = yüksek korku/panik "
        "('risk-off') — bu dönemlerde gelişen piyasalardan (BIST dahil) sermaye çıkışı hızlanır."
    ),
    "USD/TRY": (
        "1 ABD Dolarının kaç Türk Lirası ettiğini gösterir.\n\n"
        "**Yorumlama:** Yükseliş = TL değer kaybediyor (USD güçleniyor). BIST getirilerini "
        "USD bazında değerlendirirken bu kurun hareketi hisse performansından bağımsız "
        "olarak getiriyi etkiler."
    ),
    "EUR/USD": (
        "1 Euro'nun kaç ABD Doları ettiğini gösterir, iki büyük rezerv para birimi arasındaki güç dengesini yansıtır.\n\n"
        "**Yorumlama:** Yükseliş = Euro güçleniyor / Dolar zayıflıyor. Genellikle Fed ve ECB "
        "arasındaki faiz farkı beklentisine göre hareket eder."
    ),
    "USD/JPY": (
        "1 ABD Dolarının kaç Japon Yeni ettiğini gösterir.\n\n"
        "**Yorumlama:** Yükseliş = Yen zayıflıyor. Yen düşük faizi nedeniyle 'carry trade' "
        "(düşük faizli para ile borçlanıp yüksek getirili varlıklara yatırım) finansmanında "
        "sıkça kullanılır — BOJ faiz artırırsa bu işlemlerin hızla çözülmesi küresel risk "
        "iştahını olumsuz etkileyebilir."
    ),
    "USD/CNY": (
        "1 ABD Dolarının kaç Çin Yuanı ettiğini gösterir.\n\n"
        "**Yorumlama:** Yükseliş = Yuan zayıflıyor. PBOC'un kuru nasıl yönettiği (kontrollü "
        "devalüasyon sinyalleri) gelişen piyasa risk iştahını doğrudan etkileyebilir."
    ),
    "Brent Petrol": (
        "Küresel referans ham petrol fiyatı (varil başına USD).\n\n"
        "**Yorumlama:** Yükseliş, Türkiye gibi enerji ithalatçısı ülkelerde cari açığı "
        "büyütme ve TL üzerinde baskı yaratma eğilimindedir."
    ),
    "MSCI EM Proxy (Gelişen Piyasalar)": (
        "Gelişen piyasa hisselerinin genel performansını izlemek için kullanılan "
        "iShares MSCI Emerging Markets ETF (EEM) fiyatı. Not: Resmi MSCI EM Endeksi "
        "ücretsiz API'lerde doğrudan bulunmuyor, bu ETF endeksi çok yakından takip "
        "ettiği için pratik bir vekil (proxy) gösterge olarak kullanılıyor.\n\n"
        "**Yorumlama:** Yükseliş = gelişen piyasalara (Türkiye dahil) küresel yatırımcı "
        "iştahı artıyor. Düşüş = gelişen piyasalardan risk azaltma/çıkış eğilimi. "
        "BIST'in küresel EM akımlarıyla ne kadar uyumlu hareket ettiğini karşılaştırmak "
        "için faydalıdır."
    ),
}

FAIZ_GOSTERGE_BILGI = {
    "Fed Faiz Oranı (%)": (
        "ABD Merkez Bankası'nın (Federal Reserve) gecelik bankalar arası faiz oranı.\n\n"
        "**Yorumlama:** Küresel rezerv para biriminin faizi olduğu için tüm dünya sermaye "
        "akışlarını etkiler. Yükseliş genellikle gelişen piyasalardan (BIST dahil) sermaye "
        "çıkışına, USD'nin güçlenmesine yol açar."
    ),
    "ECB Faiz Oranı (%)": (
        "Avrupa Merkez Bankası'nın (ECB) mevduat faiz oranı.\n\n"
        "**Yorumlama:** Fed ile arasındaki fark (faiz farkı) EUR/USD paritesinin ana "
        "belirleyicilerinden biridir."
    ),
    "PBOC Faiz Oranı (%)": (
        "Çin Merkez Bankası'nın (PBOC) referans faiz oranı.\n\n"
        "**Yorumlama:** Çin'in büyüme görünümü ve para politikası duruşu, emtia fiyatları "
        "ve gelişen piyasa risk iştahı üzerinde doğrudan etkilidir."
    ),
    "BOJ Faiz Oranı (%)": (
        "Japonya Merkez Bankası'nın (BOJ) referans faiz oranı.\n\n"
        "**Yorumlama:** Uzun süredir çok düşük olduğu için 'carry trade' finansmanının "
        "kaynağı — BOJ'un faiz artırma sinyalleri küresel risk iştahını sarsabilir."
    ),
    "TCMB Faiz Oranı (%)": (
        "TCMB'nin politika faizi (1 haftalık repo ihale faiz oranı) — Türkiye'deki "
        "para politikasının temel aracı.\n\n"
        "**Yorumlama:** Enflasyonla mücadele için yüksek tutulduğunda TL varlıklara olan "
        "faiz cazibesini artırır ('carry' getirisi), ama aynı zamanda kredi maliyetlerini "
        "yükselterek şirket karlılığını baskılayabilir."
    ),
}

# Bir göstergenin neden otomatik çekilemediğine dair kısa gerekçe (kaynak kısıtı).
# "Manuel (yedek)" olarak görünen bir değerin yanında bu açıklama gösterilir.
MANUEL_GEREKCE = {
    "PBOC Faiz Oranı (%)": (
        "FRED'deki Çin faiz serisi OECD kaynaklı ve aylık, bazen 1 yıla kadar gecikmeli "
        "güncelleniyor — bu yüzden güncel veri çoğu zaman bulunamıyor."
    ),
    "BOJ Faiz Oranı (%)": (
        "FRED'deki Japonya faiz serisi OECD kaynaklı ve aylık, bazen 1 yıla kadar gecikmeli "
        "güncelleniyor — bu yüzden güncel veri çoğu zaman bulunamıyor."
    ),
    "TCMB Faiz Oranı (%)": (
        "TCMB, EVDS veri servisini 2025 sonunda köklü şekilde değiştirdi ve resmi API "
        "belgelenmemiş hale geldi. Kullandığımız üçüncü parti kütüphane (borsapy) bazen "
        "sayfa yapısındaki değişikliklere karşı hatalı okuma yapabiliyor; bu yüzden gelen "
        "değer makul bir aralığın (%15-%60) dışındaysa otomatik olarak güvenilmez sayılıp "
        "manuel değere düşülüyor."
    ),
    "Fed Faiz Oranı (%)": "FRED API key'i secrets.toml içinde tanımlı değil.",
    "ECB Faiz Oranı (%)": "FRED API key'i secrets.toml içinde tanımlı değil.",
}

# Manuel/otomatik gelen verileri kendi gözünle doğrulayabileceğin resmi kaynak linkleri
KAYNAK_LINKLERI = {
    "Fed Faiz Oranı (%)": "https://www.federalreserve.gov/monetarypolicy/openmarket.htm",
    "ECB Faiz Oranı (%)": "https://www.ecb.europa.eu/stats/policy_and_exchange_rates/key_ecb_interest_rates/html/index.en.html",
    "TCMB Faiz Oranı (%)": "https://www.tcmb.gov.tr/wps/wcm/connect/tr/tcmb+tr/main+menu/temel+faaliyetler/para+politikasi/politika+faizi",
    "PBOC Faiz Oranı (%)": "https://www.pbc.gov.cn/en/3688006/3688438/3688442/index.html",
    "BOJ Faiz Oranı (%)": "https://www.boj.or.jp/en/mopo/mpmdeci/index.htm",
    "TÜFE Yıllık Enflasyon (%)": "https://www.tuik.gov.tr/Kategori/GetKategori?p=Enflasyon-ve-Fiyat-106",
}

# --- Rejim yorumlama katmanının varsayılan eşik değerleri ---
# Bu değerler app.py'de kenar çubuğundan (sidebar) değiştirilebilir.
# Burada tanımlı olanlar, kullanıcı hiç dokunmazsa kullanılacak başlangıç değerleridir.
DEFAULT_ESIKLER = {
    "vix_risk_on": 20.0,       # VIX bu değerin altındaysa Risk-On
    "vix_risk_off": 30.0,      # VIX bu değerin üstündeyse Risk-Off
    "sermaye_esik": 2.0,       # USD/TRY-CNY ortalama %değişim eşiği (giriş/çıkış sinyali)
    "carry_yuksek": 10.0,      # TCMB-Fed farkı bu puanın üstündeyse "Yüksek" carry
    "carry_cok_yuksek": 20.0,  # TCMB-Fed farkı bu puanın üstündeyse "Çok Yüksek" carry
    "bist_fk_ucuz": 8.0,       # BIST ort. F/K bu değerin altındaysa "Ucuz/Makul"
    "bist_fk_pahali": 14.0,    # BIST ort. F/K bu değerin üstündeyse "Pahalı"
    "abd_fk_ucuz": 20.0,       # ABD ort. F/K bu değerin altındaysa "Ucuz/Makul"
    "abd_fk_pahali": 30.0,     # ABD ort. F/K bu değerin üstündeyse "Pahalı"
    "dxy_esik": 2.0,           # DXY %değişim eşiği (TL/EM baskı/destek sinyali)
    "tahvil_esik": 3.0,        # ABD 10Y tahvil %değişim eşiği (değerleme baskısı sinyali)
    "fed_yon_esik": 0.1,       # Fed faizi bu puandan fazla değiştiyse yön sinyali verilir
}
