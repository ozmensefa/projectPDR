# Servis Yönetimi Kılavuzu

## 🚀 Hızlı Başlangıç

### Servisleri Başlatma
```bash
./serviceStart.sh
```

### Servisleri Durdurma
```bash
./serviceStop.sh
```

## 📋 Servisler

Sistem 3 ana servisten oluşur:

1. **Redis Server** (port 6380) - Mesaj kuyruğu
2. **Celery Worker** - Arka plan görevleri
3. **Flask App** (port 8000) - Web sunucusu

## 🔧 Detaylı Kullanım

### serviceStart.sh

**Özellikler:**
- ✅ Servislerin zaten çalışıp çalışmadığını kontrol eder
- ✅ Çakışma önleme mekanizması
- ✅ Her servis için ayrı log dosyası
- ✅ Başarı/hata durumu raporlama
- ✅ Renkli terminal çıktısı

**Çalıştırma:**
```bash
cd /home/sefa4/projectPDR
./serviceStart.sh
```

**Çıktı Örneği:**
```
╔══════════════════════════════════════════════════════════════╗
║       PDR VİDEO ANALİZ SİSTEMİ - SERVİS BAŞLATMA           ║
╚══════════════════════════════════════════════════════════════╝

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1️⃣  REDIS SERVER BAŞLATILIYOR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Redis başarıyla başlatıldı (port 6380)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
2️⃣  CELERY WORKER BAŞLATILIYOR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Celery worker başarıyla başlatıldı (10 process)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
3️⃣  FLASK UYGULAMASI BAŞLATILIYOR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Flask uygulaması başarıyla başlatıldı (PID: 12345)
```

### serviceStop.sh

**Özellikler:**
- ✅ Graceful shutdown (önce nazikçe durdurma)
- ✅ Force kill mekanizması (gerekirse)
- ✅ Tüm servisler için kapsamlı kontrol
- ✅ Başarı/hata durumu raporlama
- ✅ Renkli terminal çıktısı

**Çalıştırma:**
```bash
cd /home/sefa4/projectPDR
./serviceStop.sh
```

**Çıktı Örneği:**
```
╔══════════════════════════════════════════════════════════════╗
║       PDR VİDEO ANALİZ SİSTEMİ - SERVİS DURDURMA           ║
╚══════════════════════════════════════════════════════════════╝

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1️⃣  FLASK UYGULAMASI DURDURULUYOR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Flask başarıyla durduruldu

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
2️⃣  CELERY WORKER DURDURULUYOR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Celery worker başarıyla durduruldu

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
3️⃣  REDIS SERVER DURDURULUYOR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Redis başarıyla durduruldu
```

## 📝 Log Dosyaları

Servisler aşağıdaki log dosyalarını kullanır:

```bash
logs/
├── celery_worker.log    # Celery worker logları
└── flask_app.log        # Flask uygulama logları
```

### Logları İzleme

**Celery logları:**
```bash
tail -f logs/celery_worker.log
```

**Flask logları:**
```bash
tail -f logs/flask_app.log
```

**Tüm loglar:**
```bash
tail -f logs/*.log
```

## 🔍 Durum Kontrolü

### Manuel Kontrol

**Redis:**
```bash
redis-cli -p 6380 ping
# Cevap: PONG (çalışıyor)
```

**Celery:**
```bash
ps aux | grep "celery.*worker" | grep -v grep
```

**Flask:**
```bash
ps aux | grep "python3 run.py" | grep -v grep
```

**Port kontrolü:**
```bash
netstat -tlnp | grep 8000
```

## 🔄 Yeniden Başlatma

Servisleri yeniden başlatmak için:

```bash
./serviceStop.sh && sleep 2 && ./serviceStart.sh
```

Veya:

```bash
./restart_services.sh
```

## ⚠️ Sorun Giderme

### Servis Başlamıyor

1. **Log dosyalarını kontrol edin:**
   ```bash
   tail -50 logs/celery_worker.log
   tail -50 logs/flask_app.log
   ```

2. **Port kullanımda mı kontrol edin:**
   ```bash
   netstat -tlnp | grep 6380  # Redis
   netstat -tlnp | grep 8000  # Flask
   ```

3. **Sanal ortam aktif mi kontrol edin:**
   ```bash
   which python3  # /home/sefa4/projectPDR/venv/bin/python3 olmalı
   ```

### Servis Durdurmuyor

1. **Force kill deneyin:**
   ```bash
   pkill -9 -f "celery.*worker"
   pkill -9 -f "python3 run.py"
   redis-cli -p 6380 shutdown
   ```

2. **Process ID'leri bulup manuel kill edin:**
   ```bash
   ps aux | grep celery
   kill -9 <PID>
   ```

### Port Çakışması

Eğer port zaten kullanılıyorsa:

```bash
# Port 8000'de ne çalışıyor?
lsof -i :8000

# Process'i öldür
kill -9 <PID>
```

## 🎯 Farkları

| Özellik | serviceStart.sh | restart_services.sh | start_celery.sh |
|---------|----------------|---------------------|-----------------|
| Redis | ✅ | ✅ | ❌ |
| Celery | ✅ | ✅ | ✅ |
| Flask | ✅ | ✅ | ❌ |
| Durum kontrolü | ✅ | ✅ | ❌ |
| Renkli çıktı | ✅ | ❌ | ❌ |
| Çakışma kontrolü | ✅ | ⚠️ | ❌ |
| Log yönetimi | ✅ | ✅ | ⚠️ |

**Öneri:** Genel kullanım için `serviceStart.sh` ve `serviceStop.sh` kullanın.

## 📚 İlgili Dökümanlar

- `run.txt` - Detaylı başlatma kılavuzu
- `KULLANIM_KILAVUZU.md` - Sistem kullanım kılavuzu
- `scripts/README.md` - Yardımcı scriptler rehberi

## 🚀 Production Deployment

Production ortamında systemd service olarak çalıştırmak için:

```bash
# Servis dosyalarını oluştur
sudo systemctl enable redis-pdr
sudo systemctl enable celery-pdr
sudo systemctl enable flask-pdr

# Başlat
sudo systemctl start redis-pdr celery-pdr flask-pdr

# Durum kontrol
sudo systemctl status redis-pdr celery-pdr flask-pdr
```

Detaylar için `DEPLOYMENT_CHECKLIST.md` dosyasına bakın.

---

**Oluşturulma Tarihi:** 2025-11-09  
**Versiyon:** 1.0  
**Yazar:** AI Assistant + Sefa ÖZMEN

