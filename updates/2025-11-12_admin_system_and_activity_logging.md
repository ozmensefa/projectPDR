# Admin Sistemi ve Kullanıcı Aktivite Loglama

**Tarih:** 2025-11-12  
**Versiyon:** 2.0  

## 🎯 Özet
Sisteme admin yetkilendirme ve kullanıcı aktivite loglama özellikleri eklendi. Admin kullanıcılar artık tüm kullanıcıların aktivitelerini tarih bazlı olarak görüntüleyebilir ve diğer kullanıcılara admin yetkisi verebilir/kaldırabilir. Login, logout ve diğer önemli aksiyonlar otomatik olarak loglanıyor.

## 📝 Değişiklikler

### Veritabanı
- ✏️ `app/models.py` - `Counselor` modeline `is_admin` field eklendi
- 📄 `app/models.py` - `UserActivity` modeli eklendi (aktivite logları için)

### Backend
- ✏️ `app/routes.py` - 3 yeni admin route eklendi:
  - `/admin/user-activities` - Aktivite loglarını görüntüleme
  - `/admin/manage-users` - Kullanıcı yönetimi
  - `/admin/toggle-admin/<user_id>` - Admin yetkisi toggle
- ✏️ `app/auth.py` - Login/logout aktivite logları eklendi
- 📄 `app/utils/decorators.py` - `@admin_required` decorator oluşturuldu
- 📄 `app/utils/activity.py` - `log_activity()` helper fonksiyonu oluşturuldu

### Frontend
- ✏️ `app/templates/base.html` - Admin menüsü eklendi (sarı renkli, shield ikonu)
- 📄 `app/templates/admin/user_activities.html` - Aktivite logları sayfası
- 📄 `app/templates/admin/manage_users.html` - Kullanıcı yönetimi sayfası

### Scripts
- 📄 `make_admin.py` - Admin kullanıcı oluşturma scripti
- 📄 `ADMIN_SISTEM_KILAVUZU.md` - Detaylı kullanım kılavuzu

## 🚀 Kullanım

### Veritabanı Güncelleme (Otomatik yapıldı)
```bash
cd /home/sefa4/projectPDR
source venv/bin/activate
python3 -c "from app import create_app, db; app=create_app(); app.app_context().push(); db.create_all()"
```

### İlk Admin Kullanıcı Oluşturma (Yapıldı)
```bash
python3 make_admin.py admin@gmail.com
```

### Yeni Admin Kullanıcı Ekleme
```bash
python3 make_admin.py email@example.com
```

### Mevcut Kullanıcıları Listeleme
```bash
python3 make_admin.py
```

### Kodda Aktivite Loglama
```python
from app.utils.activity import log_activity

# Örnek kullanımlar
log_activity('add_client', 'Yeni danışan eklendi: Ahmet Yılmaz')
log_activity('create_session', 'Seans oluşturuldu: İlk Görüşme')
log_activity('view_report', 'Rapor görüntülendi')
log_activity('update_profile', 'Profil güncellendi')
log_activity('delete_video', 'Video silindi')
log_activity('start_analysis', 'Analiz başlatıldı')
```

## 🎨 Özellikler

### Admin Paneli
- ✅ Sadece admin kullanıcılar erişebilir
- ✅ Tüm kullanıcıların aktivite loglarını görüntüleme
- ✅ Kullanıcılara admin yetkisi verme/kaldırma
- ✅ Filtreleme özellikleri:
  - Tarih: Bugün, Son 7 Gün, Son 30 Gün, Tümü
  - Kullanıcı bazlı
  - Aksiyon bazlı (arama)
- ✅ İstatistikler:
  - Toplam aktivite sayısı
  - Aktif kullanıcı sayısı
  - Bugünkü aktivite sayısı
- ✅ Sayfalama (pagination) desteği

### Aktivite Loglama
- ✅ Otomatik login/logout logları
- ✅ Tarih damgalı kayıtlar
- ✅ Her log için detaylı açıklama
- ✅ Kullanıcı bazlı görüntüleme
- ✅ Performans dostu (DB session yönetimi)

### Güvenlik
- ✅ `@admin_required` decorator ile route koruması
- ✅ Normal kullanıcılar admin paneline erişemez
- ✅ Kullanıcı kendi admin yetkisini kaldıramaz
- ✅ Flash mesajları ile kullanıcı geri bildirimleri

## 💡 Notlar

### Mevcut Admin Kullanıcı
- **Email:** admin@gmail.com
- **Durum:** ✅ Admin yetkisi aktif

### Otomatik Loglanan Aksiyonlar
- `login` - Kullanıcı girişi
- `logout` - Kullanıcı çıkışı
- `toggle_admin` - Admin yetkisi değişikliği

### Önerilen Ek Loglamalar
Aşağıdaki yerlere aktivite loglaması eklenebilir:

**app/client.py:**
```python
log_activity('add_client', f'{client.name} adlı danışan eklendi')
log_activity('update_client', f'{client.name} danışan güncellendi')
log_activity('delete_client', f'{client.name} danışan silindi')
```

**app/routes.py:**
```python
log_activity('create_session', f'{session.title} seansı oluşturuldu')
log_activity('view_session', f'{session.title} seansı görüntülendi')
log_activity('start_video_analysis', f'Seans #{session_id} video analizi başlatıldı')
log_activity('view_progress_report', f'{client.name} ilerleme raporu görüntülendi')
log_activity('delete_video', f'Seans #{session_id} videosu silindi')
```

### Veritabanı Tabloları

**counselor tablosu:**
- Yeni kolon: `is_admin` (BOOLEAN, default: FALSE)

**user_activity tablosu (YENİ):**
```sql
CREATE TABLE user_activity (
    id INTEGER PRIMARY KEY,
    counselor_id INTEGER NOT NULL,
    action VARCHAR(100) NOT NULL,
    description VARCHAR(500),
    created_at DATETIME NOT NULL,
    FOREIGN KEY (counselor_id) REFERENCES counselor(id)
);
CREATE INDEX ix_user_activity_created_at ON user_activity(created_at);
```

### Gelecek İyileştirmeler
- [ ] GDPR uyumlu otomatik log temizleme (X gün sonra)
- [ ] CSV/Excel export özelliği
- [ ] Real-time aktivite bildirimleri
- [ ] Şüpheli aktivite uyarıları
- [ ] Detaylı aktivite raporları
- [ ] IP adresi ve user agent bilgileri
- [ ] Aktivite istatistik grafikleri

### Önemli
- Servisler yeniden başlatıldı ve sistem aktif
- Veritabanı güncellemeleri otomatik yapıldı
- Favicon da güncellendi (mavi Y logosu)
- Tüm değişiklikler production'da aktif

## 🔗 İlgili Dosyalar
- `ADMIN_SISTEM_KILAVUZU.md` - Detaylı kullanım kılavuzu
- `make_admin.py` - Admin yönetim scripti

---

**Geliştirici:** Cursor AI Assistant  
**Test Durumu:** ✅ Test edildi ve çalışıyor  
**Production Durumu:** ✅ Aktif

