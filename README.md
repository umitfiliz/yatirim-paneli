# Yatırım Karar Destek Paneli

BIST ve ABD hisseleri için 3 katmanlı karar destek sistemi.

## Yerel Bilgisayarında Test Etme

1. Bu klasördeki tüm dosyaları bilgisayarına indir.
2. Terminal/komut satırında klasöre gir:
   ```
   cd yatirim-paneli
   ```
3. Gerekli kütüphaneleri kur:
   ```
   pip install -r requirements.txt
   ```
   (pip tanınmıyorsa `python -m pip install -r requirements.txt` kullan)
4. **API key'lerini tanımla (Katman 1'in otomatik çalışması için gerekli):**
   - Bu klasörün içinde `.streamlit` adında bir klasör oluştur
   - İçine `secrets.toml` adında bir dosya oluştur
   - `secrets.toml.example` dosyasındaki içeriği kopyala, kendi gerçek key'lerinle doldur
   - Bu adımı atlarsan uygulama yine çalışır ama Katman 1'de manuel/yedek değerler gösterilir
5. Uygulamayı çalıştır:
   ```
   streamlit run app.py
   ```
   (streamlit tanınmıyorsa `python -m streamlit run app.py` kullan)
6. Tarayıcıda otomatik olarak `http://localhost:8501` açılacak.

## GitHub'a Yükleme ve Streamlit Cloud'da Yayınlama

1. GitHub'da yeni bir repo oluştur (örn. `yatirim-paneli`).
2. **`.streamlit/secrets.toml` dosyasını GitHub'a YÜKLEME** — `.gitignore` bunu zaten engelliyor, ama kontrol et. Diğer tüm dosyaları (`app.py`, `config.py`, `data_utils.py`, `macro_utils.py`, `requirements.txt`, `.gitignore`, `secrets.toml.example`, `README.md`) yükle.
3. [share.streamlit.io](https://share.streamlit.io) adresine git, GitHub hesabınla giriş yap.
4. "New app" > reponu seç > main dosya olarak `app.py` göster.
5. **Deploy etmeden önce** "Advanced settings" > "Secrets" bölümüne, `secrets.toml.example`'daki formatta gerçek key'lerini yapıştır.
6. Deploy et. Birkaç dakika içinde uygulaman `https://[senin-secimin].streamlit.app` adresinde
   yayında olacak — telefon, tablet, bilgisayar fark etmeksizin bu linkten erişebilirsin.

## Şu Anki Durum (v2)

- ✅ Katman 1: Piyasa göstergeleri (VIX, USD/TRY, EUR/USD, USD/JPY, USD/CNY, Brent) — yfinance üzerinden otomatik
- ✅ Katman 1: Politika faizleri (Fed, ECB, TCMB) — FRED ve EVDS API'lerinden otomatik çekiliyor (key tanımlıysa)
- ⚠️ Katman 1: PBOC ve BOJ faizleri FRED'de aylık ve gecikmeli güncellenen OECD serilerinden geliyor — gerçek zamanlı değil, yaklaşık gösterge olarak değerlendir
- ✅ Katman 2: Altın, USD/TRY, ABD 10 yıllık tahvil faizi karşılaştırması
- ✅ Katman 3: BIST getirileri hem USD hem TL bazlı gösteriliyor
- ✅ Katman 3: ABD hisseleri zaten USD bazlı

## Sıradaki Adımlar

- Temel analiz metrikleri (F/K, PD/DD) ekleme
- Risk-ayarlı getiri (volatilite, Sharpe oranı) hesaplama
- MSCI EM Endeksi / EMBI spread gibi gelişen piyasa risk göstergesi ekleme
- Enflasyon verisiyle reel faiz hesaplama (TÜFE serisi zaten `macro_utils.py`'de tanımlı, kullanılmayı bekliyor)
