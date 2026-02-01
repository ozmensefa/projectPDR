# 📘 İlerleyiş Analizi Düzeltme Kılavuzu

**Tarih:** 2025-11-07  
**Durum:** Hazır

## 🎯 Yapılan Değişiklikler

### Kod Değişiklikleri
✅ `app/routes.py` - Task başlatma yöntemi değiştirildi  
✅ Oturum ve ilerleyiş analizleri tutarlı hale getirildi  
✅ `celery.send_task()` yöntemi kullanıldı

### Neden?
- ❌ `analyze_progress.delay()` - Import hatası
- ✅ `celery.send_task()` - Güvenli ve çalışıyor

## 🚀 Sunucuda Yapılacaklar

### Google Cloud SSH'ye Bağlan
```bash
# Google Cloud Console'dan SSH butonu ile bağlan
```

### Adım 1: Kod Değişiklikleri Yapıldı mı Kontrol Et
```bash
cd /home/sefa4/projectPDR
grep "celery.send_task" app/routes.py
```

**Görmeli siniz:**
```python
task = celery.send_task(
    'app.tasks.analyze_progress',
```

**Eğer görmüyorsanız**, kod değişiklikleri henüz kaydedilmemiş demektir.

### Adım 2: Servisleri Yeniden Başlat
```bash
chmod +x RESTART_SERVICES.sh
./RESTART_SERVICES.sh
```

**Beklenen Çıktı:**
```
✅ SERVİSLER YENİDEN BAŞLATILDI!
📊 Durum Özeti:
   • Gunicorn: 3 process
   • Celery: 3 process
   • Redis: PONG
```

### Adım 3: Test Et
```bash
# Yeni analiz oluşturduktan sonra
./check_analysis.sh
```

**Görmeli siniz:**
```
📊 Son 5 dakikada 1 analiz:

  ID: XX
  Status: processing
  Progress: 10%
  Task ID: abc-123-xyz  ← ÖNEMLİ!
```

## 🔍 Sorun Giderme

### Problem: Task ID hala None

**Çözüm 1:** Kod değişikliği kontrol et
```bash
grep "send_task" app/routes.py | head -3
```

**Çözüm 2:** Servisleri tekrar başlat
```bash
./RESTART_SERVICES.sh
```

### Problem: Celery task kayıtlı değil

**Kontrol:**
```bash
cd /home/sefa4/projectPDR && source venv/bin/activate
celery -A app.celery_config.celery inspect registered | grep analyze_progress
```

**Görmeli siniz:**
```
* app.tasks.analyze_progress
```

**Görmüyorsanız:**
```bash
pkill -9 -f celery
cd /home/sefa4/projectPDR && source venv/bin/activate
nohup celery -A app.celery_config.celery worker --loglevel=info --concurrency=2 > logs/celery.log 2>&1 &
```

### Problem: Duplicate node warning

**Çözüm:** Çoklu Celery var, hepsini temizle
```bash
pkill -9 -f celery
sleep 3
./RESTART_SERVICES.sh
```

## 📊 Logları İzleme

### Celery Log
```bash
tail -f /home/sefa4/projectPDR/logs/celery.log
```

**Başarılı task:**
```
🚀 ARKA PLAN İLERLEYİŞ ANALİZİ BAŞLADI
📋 Task ID: xxx-yyy-zzz
📝 Danışan: Ali Yılmaz
📊 3 oturum bulundu
✅ 3 oturum verisi hazırlandı
🤖 AI İLE İLERLEYİŞ ANALİZİ BAŞLIYOR...
```

### Gunicorn Log
```bash
tail -f /home/sefa4/projectPDR/logs/gunicorn.log
```

## ✅ Başarı Kriterleri

1. ✅ Task ID dolu (None değil)
2. ✅ Status: processing (pending değil)
3. ✅ Celery log'da task görünüyor
4. ✅ İlerleme %0 → %100
5. ✅ Bildirim geliyor
6. ✅ Rapor görüntüleniyor

## 🎯 Özet Komutlar

```bash
# 1. Servisleri başlat
./RESTART_SERVICES.sh

# 2. Analiz oluştur (Web'de)

# 3. Kontrol et
./check_analysis.sh

# 4. Log izle
tail -f logs/celery.log
```

## 💡 Notlar

- Her kod değişikliğinden sonra servisleri yeniden başlatın
- Sadece TEK Gunicorn ve TEK Celery çalışmalı
- Redis sürekli çalışmalı
- Task'lar kayıtlı olmalı

---

**Hazırlayan:** AI Assistant  
**Versiyon:** 2.2  
**Tarih:** 2025-11-07

