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

## Şu Anki Durum (v6)

- ✅ Katman 1: Piyasa göstergeleri, politika faizleri, Rejim Özeti, Ülkeye Özgü Faktörler, ayarlanabilir eşikler
- ✅ Katman 2: **Varlık Sınıfı Karşılaştırması** — BIST hisseleri (ort.), ABD hisseleri (ort.), Altın, TL Mevduatı (yaklaşık), USD/TRY referansı tek tabloda ve gruplu çubuk grafikte karşılaştırılıyor; en yüksek/en düşük getiri otomatik vurgulanıyor
- ✅ Katman 2: TL Mevduatı, TCMB politika faizinden basit faiz yaklaşımıyla türetilip USD/TRY değişimiyle USD bazına çevriliyor (bileşik faiz değil, yaklaşık bir hesaplama — açıkça belirtiliyor)
- ✅ Katman 3: BIST/ABD hisse bazlı getiriler (USD/TL)
- ✅ GitHub + Streamlit Cloud üzerinden yayında, çok cihazdan erişilebilir

## Sıradaki Adımlar

- Risk-ayarlı getiri (volatilite, Sharpe oranı) hesaplama
- EMBI spread gibi ek bir EM risk göstergesi
- Katman 3'te F/K, PD/DD gibi metrikleri tek tek hisse bazında gösterme
- Kenar çubuğundaki eşik ayarlarını bir profil olarak kaydedip yeniden yükleyebilme
