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

## Şu Anki Durum (v4)

- ✅ Katman 1: Piyasa göstergeleri (VIX, USD/TRY, EUR/USD, USD/JPY, USD/CNY, Brent, MSCI EM proxy) — yfinance üzerinden otomatik
- ✅ Katman 1: Politika faizleri (Fed, ECB, TCMB) — FRED ve borsapy üzerinden otomatik
- ✅ Katman 1: **Rejim Özeti** — küresel ham verileri yorumlayan puanlama tabanlı bir sentez, bileşen dökümüyle şeffaf
- ✅ Katman 1: **Ülkeye Özgü Faktörler** — BIST ve ABD için ayrı ayrı: TÜFE/reel faiz, ortalama F/K değerlemesi, DXY, ABD tahvil trendi. İki ayrı bağlam ("BIST Bağlamı" / "ABD Bağlamı") üretiliyor
- ⚠️ Katman 1: PBOC ve BOJ faizleri FRED'de aylık ve gecikmeli güncellenen OECD serilerinden geliyor — gerçek zamanlı değil
- ✅ Katman 2: Altın, USD/TRY, ABD 10 yıllık tahvil faizi karşılaştırması + Katman 1'den gelen küresel + ülkeye özgü bağlam
- ✅ Katman 3: BIST getirileri hem USD hem TL bazlı gösteriliyor
- ✅ Katman 3: ABD hisseleri zaten USD bazlı
- ✅ GitHub + Streamlit Cloud üzerinden yayında, çok cihazdan erişilebilir

## Sıradaki Adımlar

- Risk-ayarlı getiri (volatilite, Sharpe oranı) hesaplama
- EMBI spread gibi ek bir EM risk göstergesi (şu an sadece MSCI EM proxy var)
- Katman 3'te F/K, PD/DD gibi metrikleri tek tek hisse bazında (şu an sadece ortalama olarak Katman 1'de kullanılıyor) gösterme
