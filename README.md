# YerelEtkinlik

Yerel etkinlikleri keşfetmek ve paylaşmak için bir web uygulaması.

## Kurulum

1. Gerekli paketleri yükleyin:
```bash
pip install -r requirements.txt
```

2. `.env` dosyasını oluşturun:
```
SECRET_KEY=your-secret-key
FLASK_ENV=production
FLASK_APP=app.py
DATABASE_URL=sqlite:///instance/etkinlik.db
```

3. Veritabanını oluşturun:
```bash
flask db upgrade
```

4. Uygulamayı çalıştırın:
```bash
flask run
```

## Güvenlik

- Tüm hassas bilgiler `.env` dosyasında saklanır
- Veritabanı dosyaları `instance/` klasöründe tutulur
- Kullanıcı yüklemeleri `static/uploads/` klasöründe saklanır

## Lisans

Bu proje özel kullanım içindir. İzinsiz kopyalanması ve dağıtılması yasaktır. 