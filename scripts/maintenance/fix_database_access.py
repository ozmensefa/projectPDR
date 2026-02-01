# -*- coding: utf-8 -*-
"""
Veritabanı erişim sorununu çöz (veriyi koruyarak)
"""
import os
import shutil
from datetime import datetime

def fix_database_access():
    print("\n" + "="*60)
    print("VERİTABANI ERİŞİM SORUNU ÇÖZÜLÜYOR")
    print("="*60 + "\n")
    
    db_path = '/home/sefa4/projectPDR/instance/app.db'
    instance_path = '/home/sefa4/projectPDR/instance'
    
    # 1. Instance klasörünü kontrol et
    print("1. Instance klasörü kontrol ediliyor...")
    if not os.path.exists(instance_path):
        print(f"   ⚠️  Instance klasörü yok, oluşturuluyor: {instance_path}")
        os.makedirs(instance_path, mode=0o755)
        print("   ✅ Instance klasörü oluşturuldu")
    else:
        print(f"   ✅ Instance klasörü mevcut")
    
    # 2. Veritabanı dosyasını kontrol et
    print("\n2. Veritabanı dosyası kontrol ediliyor...")
    if os.path.exists(db_path):
        print(f"   ✅ Veritabanı mevcut: {db_path}")
        
        # Dosya boyutunu göster
        size = os.path.getsize(db_path)
        print(f"   📊 Boyut: {size:,} bytes ({size/1024:.2f} KB)")
        
        # İzinleri kontrol et
        stat_info = os.stat(db_path)
        print(f"   🔐 İzinler: {oct(stat_info.st_mode)[-3:]}")
        
    else:
        print(f"   ❌ Veritabanı bulunamadı: {db_path}")
        print("   Veritabanı yeni oluşturulacak")
        return False
    
    # 3. Yedek al
    print("\n3. Güvenlik yedeği alınıyor...")
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    try:
        shutil.copy2(db_path, backup_path)
        print(f"   ✅ Yedek alındı: {backup_path}")
    except Exception as e:
        print(f"   ⚠️  Yedek alınamadı: {e}")
    
    # 4. İzinleri düzelt
    print("\n4. İzinler düzeltiliyor...")
    try:
        # Instance klasörü izinleri
        os.chmod(instance_path, 0o755)
        print(f"   ✅ Instance klasörü izinleri: 755")
        
        # Veritabanı dosyası izinleri
        os.chmod(db_path, 0o644)
        print(f"   ✅ Veritabanı izinleri: 644")
        
        # Sahipliği kontrol et
        import pwd
        file_owner = pwd.getpwuid(os.stat(db_path).st_uid).pw_name
        current_user = os.getenv('USER')
        print(f"   👤 Dosya sahibi: {file_owner}")
        print(f"   👤 Mevcut kullanıcı: {current_user}")
        
        if file_owner != current_user:
            print(f"   ⚠️  Sahiplik farklı, chown gerekebilir")
            
    except Exception as e:
        print(f"   ⚠️  İzin düzeltme hatası: {e}")
    
    # 5. Veritabanı bütünlüğünü test et
    print("\n5. Veritabanı bütünlüğü test ediliyor...")
    try:
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # PRAGMA integrity_check
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()
        if result[0] == 'ok':
            print("   ✅ Veritabanı bütünlüğü: OK")
        else:
            print(f"   ⚠️  Bütünlük sorunu: {result[0]}")
        
        # Tabloları listele
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"   📊 {len(tables)} tablo bulundu:")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cursor.fetchone()[0]
            print(f"      - {table[0]}: {count} kayıt")
        
        conn.close()
        
    except Exception as e:
        print(f"   ❌ Veritabanı test hatası: {e}")
        return False
    
    print("\n" + "="*60)
    print("✅ VERİTABANI ERİŞİM SORUNU ÇÖZÜLDÜ!")
    print("="*60)
    print("\nŞimdi Flask'ı başlatabilirsiniz:")
    print("  python3 run.py")
    
    return True

if __name__ == '__main__':
    success = fix_database_access()
    exit(0 if success else 1)

