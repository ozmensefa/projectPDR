# 🚀 PDR Video Analiz Sistemi - Deployment Checklist

## ✅ Ön Hazırlık

### 1. Sunucu Gereksinimleri
- [ ] Ubuntu 22.04 LTS veya benzeri Linux sunucu
- [ ] Minimum 8GB RAM, 4 vCPU
- [ ] 100GB+ disk alanı
- [ ] Python 3.10+
- [ ] Redis 6.0+
- [ ] Nginx
- [ ] Domain adı ve SSL sertifikası

### 2. Yerel Hazırlık
- [ ] Tüm değişiklikler commit edildi
- [ ] `.gitignore` dosyası yapılandırıldı
- [ ] `non-necessary` klasörü deployment'a dahil edilmeyecek
- [ ] Gereksiz dosyalar temizlendi

---

## 📦 Dosya Transferi

### Yüklenecek Dosyalar/Klasörler:
```
✅ app/                    (Uygulama kodu)
✅ scripts/                (Utility scriptler)
✅ celery_worker.py        (Celery worker)
✅ migrate_database.py     (DB migration)
✅ requirements.txt        (Dependencies)
✅ run.py                  (Ana uygulama)
✅ run.txt                 (Deployment dokümantasyonu)
✅ start_celery.bat        (Windows için)
✅ start_celery.sh         (Linux için)
✅ .gitignore              (Git yapılandırması)
```

### Yüklenmeyecekler:
```
❌ non-necessary/          (Tüm gereksiz dosyalar)
❌ instance/app.db         (Development DB)
❌ __pycache__/            (Python cache)
❌ *.pyc, *.pyo            (Compiled Python)
❌ .env                    (Local environment)
```

---

## 🔧 Sunucu Kurulumu

### 1. Sistem Paketleri
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.10 python3.10-venv python3-pip
sudo apt install -y nginx redis-server supervisor
sudo apt install -y ffmpeg git curl
```

### 2. Redis Kurulumu
```bash
sudo systemctl enable redis-server
sudo systemctl start redis-server
redis-cli ping  # PONG dönmeli
```

### 3. Proje Klasörü
```bash
sudo mkdir -p /var/www/pdr-app
sudo chown -R $USER:$USER /var/www/pdr-app
cd /var/www/pdr-app
```

### 4. Virtual Environment
```bash
python3.10 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn
```

---

## ⚙️ Yapılandırma

### 1. Environment Variables (.env dosyası oluştur)
```bash
cat > .env << 'EOF'
SECRET_KEY=[GÜÇLÜ BİR GİZLİ ANAHTAR]
REDIS_URL=redis://localhost:6379/0
DATABASE_URL=sqlite:////var/www/pdr-app/instance/app.db
FLASK_ENV=production
EOF
```

**ÖNEMLİ:** `SECRET_KEY` için:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 2. Klasör İzinleri
```bash
mkdir -p instance uploads temp_files
chmod 755 instance uploads temp_files
```

### 3. Database Migration
```bash
python migrate_database.py
```

### 4. Admin Kullanıcı Oluştur
```bash
python scripts/create_admin.py
```

---

## 🔐 Güvenlik Yapılandırması

### 1. Firewall
```bash
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw enable
```

### 2. Dosya İzinleri
```bash
chmod 600 .env
chmod 755 start_celery.sh
chown -R www-data:www-data uploads/ temp_files/
```

### 3. Config Güncellemeleri
`app/config.py` dosyasında:
```python
# DEBUG = False olmalı
# SECRET_KEY environment'tan alınmalı
# GEMINI_API_KEY environment'tan alınmalı
```

---

## 🌐 NGINX Yapılandırması

### 1. Site Yapılandırması
```bash
sudo nano /etc/nginx/sites-available/pdr-app
```

İçerik:
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    client_max_body_size 500M;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_connect_timeout 600;
        proxy_send_timeout 600;
        proxy_read_timeout 600;
    }
    
    location /static {
        alias /var/www/pdr-app/app/static;
        expires 30d;
    }
}
```

### 2. Aktifleştir
```bash
sudo ln -s /etc/nginx/sites-available/pdr-app /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 🔄 Systemd Servisleri

### 1. Flask App Servisi
```bash
sudo nano /etc/systemd/system/pdr-app.service
```

```ini
[Unit]
Description=PDR Flask Application
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/pdr-app
Environment="PATH=/var/www/pdr-app/venv/bin"
EnvironmentFile=/var/www/pdr-app/.env
ExecStart=/var/www/pdr-app/venv/bin/gunicorn \
    --workers 4 \
    --bind 127.0.0.1:8000 \
    --timeout 600 \
    --max-requests 1000 \
    run:app

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 2. Celery Worker Servisi
```bash
sudo nano /etc/systemd/system/celery-worker.service
```

```ini
[Unit]
Description=Celery Worker
After=network.target redis.service

[Service]
Type=forking
User=www-data
Group=www-data
WorkingDirectory=/var/www/pdr-app
Environment="PATH=/var/www/pdr-app/venv/bin"
EnvironmentFile=/var/www/pdr-app/.env
ExecStart=/var/www/pdr-app/venv/bin/celery \
    -A app.celery_config.celery worker \
    --loglevel=info \
    --concurrency=2

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 3. Servisleri Başlat
```bash
sudo systemctl daemon-reload
sudo systemctl enable pdr-app celery-worker redis-server nginx
sudo systemctl start pdr-app celery-worker
sudo systemctl restart nginx
```

---

## 🔒 SSL Sertifikası (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
sudo certbot renew --dry-run  # Test otomatik yenileme
```

---

## 📊 Monitoring ve Logs

### Log Dosyaları
```bash
# Flask logs
sudo journalctl -u pdr-app -f

# Celery logs
sudo journalctl -u celery-worker -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Sistem Durumu
```bash
sudo systemctl status pdr-app
sudo systemctl status celery-worker
sudo systemctl status redis-server
sudo systemctl status nginx
```

---

## 🧪 Test

### 1. Uygulama Erişim
```bash
curl http://localhost:8000
curl https://yourdomain.com
```

### 2. Redis Bağlantısı
```bash
redis-cli ping
```

### 3. Celery Worker
```bash
# Celery worker loglarında şunları görmelisiniz:
# ✅ "celery@hostname ready"
# ✅ "Connected to redis://localhost:6379/0"
```

### 4. Video Analizi
- Admin paneline giriş yapın
- Bir danışan oluşturun
- Bir oturum ekleyin
- Video yükleyin
- Analizi başlatın
- Bildirimleri kontrol edin

---

## 🔄 Güncelleme Prosedürü

```bash
# 1. Yeni kodu çek
cd /var/www/pdr-app
git pull origin main

# 2. Dependencies güncelle
source venv/bin/activate
pip install -r requirements.txt

# 3. Database migration (gerekirse)
python migrate_database.py

# 4. Servisleri restart et
sudo systemctl restart pdr-app
sudo systemctl restart celery-worker
```

---

## 🛟 Sorun Giderme

### Problem: Port 8000 kullanımda
```bash
sudo lsof -i :8000
sudo kill -9 [PID]
sudo systemctl restart pdr-app
```

### Problem: Celery bağlanamıyor
```bash
sudo systemctl status redis-server
redis-cli ping
# .env dosyasındaki REDIS_URL'i kontrol et
```

### Problem: Permission denied
```bash
sudo chown -R www-data:www-data /var/www/pdr-app
sudo chmod -R 755 /var/www/pdr-app
```

### Problem: Video upload hatası
```bash
sudo mkdir -p /var/www/pdr-app/uploads
sudo chown -R www-data:www-data /var/www/pdr-app/uploads
sudo chmod 755 /var/www/pdr-app/uploads
```

---

## 📝 Son Kontroller

- [ ] Uygulama çalışıyor (https://yourdomain.com erişilebilir)
- [ ] SSL sertifikası aktif (HTTPS)
- [ ] Redis çalışıyor
- [ ] Celery worker çalışıyor
- [ ] Video upload çalışıyor
- [ ] Analiz sistemi çalışıyor
- [ ] Bildirimler geliyor
- [ ] Loglar düzgün yazılıyor
- [ ] Backup sistemi kuruldu
- [ ] Monitoring kuruldu

---

## 🎉 Deployment Tamamlandı!

**Sonraki Adımlar:**
1. ✅ Düzenli backup planı oluştur
2. ✅ Monitoring/alerting kur (Uptime Robot, Sentry vb.)
3. ✅ CDN kullanımını değerlendir (Cloudflare)
4. ✅ Database backup otomasyonu
5. ✅ Log rotation yapılandır

---

**Oluşturma Tarihi:** 2025-11-03
**Versiyon:** 1.0
**Deployment Tipi:** Production

