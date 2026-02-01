# 🔐 Admin Sistemi ve Kullanıcı Aktivite Loglama Kılavuzu

## 📋 Genel Bakış

Sisteme admin yetkisi ve kullanıcı aktivite loglama özellikleri eklenmiştir.

## ✨ Özellikler

### 1. Admin Yetkilendirme Sistemi
- ✅ Kullanıcılara admin yetkisi verme/kaldırma
- ✅ Admin paneline özel erişim kontrolü
- ✅ Admin menüsü (sarı renkli shield ikonu ile)

### 2. Kullanıcı Aktivite Loglama
- ✅ Tüm kullanıcı hareketlerinin tarih bazlı kaydı
- ✅ Login/Logout logları otomatik
- ✅ Filtreleme: Tarih, kullanıcı, aksiyon
- ✅ Sadece adminler tüm logları görebilir

## 🚀 Kullanım

### Admin Kullanıcı Oluşturma

Bir kullanıcıyı admin yapmak için:

```bash
cd /home/sefa4/projectPDR
source venv/bin/activate
python3 make_admin.py kullanici@email.com
```

Mevcut kullanıcıları görmek için:

```bash
python3 make_admin.py
```

### Admin Paneli

Admin kullanıcı giriş yaptığında:
1. Navbar'da **"Admin"** menüsü görünür (sarı renk)
2. İki seçenek sunar:
   - **Kullanıcı Aktiviteleri**: Tüm aktivite logları
   - **Kullanıcı Yönetimi**: Admin yetkisi ver/kaldır

### Aktivite Loglama

Kodunuzda kullanıcı aktivitelerini loglamak için:

```python
from app.utils.activity import log_activity

# Örnek kullanımlar
log_activity('add_client', 'Yeni danışan eklendi: Ahmet Yılmaz')
log_activity('create_session', 'Seans oluşturuldu: İlk Görüşme')
log_activity('view_report', 'Rapor görüntülendi')
log_activity('update_profile', 'Profil güncellendi')
```

## 📊 Veritabanı Değişiklikleri

### Yeni Kolon
- `counselor.is_admin` (BOOLEAN): Admin yetkisi

### Yeni Tablo
- `user_activity`: Kullanıcı aktivite logları
  - `id`: Primary key
  - `counselor_id`: Kullanıcı ID
  - `action`: Aksiyon (login, logout, add_client vb.)
  - `description`: Detaylı açıklama
  - `created_at`: Tarih/saat

## 📁 Eklenen Dosyalar

```
app/
├── utils/
│   ├── decorators.py          # @admin_required decorator
│   └── activity.py            # log_activity() fonksiyonu
├── templates/
│   └── admin/
│       ├── user_activities.html    # Aktivite logları sayfası
│       └── manage_users.html       # Kullanıcı yönetimi sayfası
└── models.py                  # UserActivity modeli eklendi

make_admin.py                  # Admin oluşturma scripti
```

## 🔧 Güncellenmiş Dosyalar

- `app/models.py`: UserActivity modeli, Counselor.is_admin field
- `app/routes.py`: Admin route'ları eklendi
- `app/auth.py`: Login/logout aktivite logları
- `app/templates/base.html`: Admin menüsü eklendi

## 🎯 Örnek Senaryolar

### Senaryo 1: İlk Admin Oluşturma
```bash
python3 make_admin.py admin@gmail.com
```

### Senaryo 2: Aktivite Loglarını Görüntüleme
1. Admin kullanıcı ile giriş yap
2. Navbar'da "Admin" → "Kullanıcı Aktiviteleri"
3. Filtreleri kullan: Bugün, Son 7 Gün, Son 30 Gün
4. Belirli kullanıcıyı seç
5. Aksiyon ara

### Senaryo 3: Yeni Admin Ekleme
1. Admin kullanıcı ile giriş yap
2. "Admin" → "Kullanıcı Yönetimi"
3. Kullanıcının yanındaki "Admin Yap" butonuna tıkla

### Senaryo 4: Kodda Aktivite Loglama
```python
from app.utils.activity import log_activity

@main_bp.route('/special-action')
@login_required
def special_action():
    # İşleminiz
    result = do_something()
    
    # Aktivite logla
    log_activity('special_action', 'Özel işlem gerçekleştirildi')
    
    return jsonify({'status': 'success'})
```

## 🛡️ Güvenlik

- `@admin_required` decorator ile korumalı route'lar
- Normal kullanıcılar admin paneline erişemez
- Kullanıcı kendi admin yetkisini kaldıramaz
- Tüm aktiviteler tarih damgalı olarak kaydedilir

## 📈 İstatistikler

Admin panelinde gösterilen istatistikler:
- Toplam aktivite sayısı
- Aktif kullanıcı sayısı
- Bugünkü aktivite sayısı

## ⚙️ Yapılandırma

Herhangi bir ekstra yapılandırma gerekmez. Sistem otomatik olarak:
- Login/logout'ları loglar
- Admin menüsünü sadece adminlere gösterir
- Aktiviteleri veritabanına kaydeder

## 🎓 Mevcut Admin Kullanıcı

✅ **admin** (admin@gmail.com) - İlk admin kullanıcı oluşturuldu

## 📞 Notlar

- Aktivite logları otomatik olarak birikir
- Eski logları temizlemek için periyodik bir temizleme scripti eklenebilir
- GDPR uyumluluğu için X gün sonra otomatik silme eklenebilir

---

**Tarih:** 12 Kasım 2025
**Versiyon:** 1.0
**Durum:** ✅ Aktif ve Çalışıyor

