# Scripts Klasörü

Bu klasör, PDR Video Analiz Sistemi için yardımcı scriptleri içerir.

## 📁 Klasör Yapısı

### `/maintenance/` - Bakım ve Düzeltme Scriptleri
Veritabanı ve sistem sorunlarını düzelten scriptler.

| Script | Açıklama | Kullanım |
|--------|----------|----------|
| `fix_analysis_text_column.py` | analysis_text sütununu nullable yapar | `python3 scripts/maintenance/fix_analysis_text_column.py` |
| `fix_created_at_column.py` | created_at sütunundaki UUID değerlerini düzeltir | `python3 scripts/maintenance/fix_created_at_column.py` |
| `fix_database_access.py` | Veritabanı erişim izinlerini düzeltir | `python3 scripts/maintenance/fix_database_access.py` |
| `fix_null_created_at.py` | NULL created_at değerlerini düzeltir | `python3 scripts/maintenance/fix_null_created_at.py` |
| `fix_progress_analysis.py` | İlerleyiş analizi sorunlarını otomatik düzeltir | `python3 scripts/maintenance/fix_progress_analysis.py` |
| `force_fix_database.py` | progress_analysis tablosunu yeniden oluşturur (veri yedekleyerek) | `python3 scripts/maintenance/force_fix_database.py` |
| `recreate_database.py` | Tüm veritabanını sıfırdan oluşturur | `python3 scripts/maintenance/recreate_database.py` |
| `migrate_database.py` | Veritabanı şemasını günceller | `python3 scripts/maintenance/migrate_database.py` |
| `migrate_utc_to_local.py` | UTC tarihlerini Türkiye saatine (UTC+3) çevirir | `python3 scripts/maintenance/migrate_utc_to_local.py` |

### `/testing/` - Test Scriptleri
Sistem bileşenlerini test eden scriptler.

| Script | Açıklama | Kullanım |
|--------|----------|----------|
| `test_celery_setup.py` | Celery kurulumunu test eder | `python3 scripts/testing/test_celery_setup.py` |
| `test_progress_analysis.py` | İlerleyiş analizi sistemini test eder | `python3 scripts/testing/test_progress_analysis.py` |
| `test_progress_system.py` | **Tüm sistem bileşenlerini** kapsamlı test eder | `python3 scripts/testing/test_progress_system.py` |
| `manuel_test_progress.py` | Manuel ilerleyiş analizi oluşturur ve canlı izler | `python3 scripts/testing/manuel_test_progress.py` |
| `debug_progress_analysis.py` | İlerleyiş analizi debug için kullanılır | `python3 scripts/testing/debug_progress_analysis.py` |

### `/deprecated/` - Eski/Kullanılmayan Dosyalar
Artık kullanılmayan ama yedek olarak saklanan dosyalar.

- `celery_worker.py` - Eski celery başlatıcı
- `check_analysis.sh` - Eski kontrol scripti
- `quick_start.sh` - restart_services.sh ile değiştirildi
- `restart_all.sh` - restart_services.sh ile değiştirildi
- `RESTART_SERVICES.sh` - Küçük harfli versiyon kullanılıyor
- `start_celery.bat` - Windows scripti (Linux'ta gereksiz)

### `/create_admin.py` - Yönetici Hesabı Oluşturma
İlk kurulumda admin hesabı oluşturmak için kullanılır.

```bash
python3 scripts/create_admin.py
```

## 🚀 Önerilen Kullanım Sırası

### İlk Kurulum:
1. `scripts/create_admin.py` - Admin hesabı oluştur
2. Ana dizindeki `restart_services.sh` - Servisleri başlat

### Sorun Giderme:
1. `scripts/testing/test_progress_system.py` - Sistemi test et
2. Sorunlu bileşene göre ilgili fix scriptini çalıştır
3. `scripts/testing/test_progress_system.py` - Tekrar test et

### Veritabanı Sorunları:
1. `scripts/maintenance/fix_database_access.py` - Erişim sorunları için
2. `scripts/maintenance/fix_progress_analysis.py` - İlerleyiş analizi sorunları için
3. `scripts/maintenance/migrate_database.py` - Şema güncellemeleri için

## ⚠️ Dikkat Edilmesi Gerekenler

- **Her script çalıştırılmadan önce veritabanı yedeği alınmalıdır!**
- Scripts çalıştırılırken sanal ortam aktif olmalıdır: `source venv/bin/activate`
- Bazı scriptler Flask ve Celery'nin yeniden başlatılmasını gerektirir
- `recreate_database.py` scripti TÜM VERİYİ SİLER - dikkatli kullanın!

## 📝 Not

Bu scriptler geliştirme ve bakım sürecinde oluşturulmuştur. Production ortamında kullanmadan önce test ortamında deneyin.

