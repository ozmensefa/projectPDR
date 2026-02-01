# -*- coding: utf-8 -*-
"""
created_at sütunundaki hatalı UUID değerlerini düzelt
"""
import sqlite3
from datetime import datetime

def fix_created_at():
    db_path = '/home/sefa4/projectPDR/instance/app.db'
    
    print("\n" + "="*60)
    print("CREATED_AT SÜTUNU DÜZELTİLİYOR")
    print("="*60 + "\n")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # progress_analysis tablosundaki hatalı kayıtları bul
        print("1. Hatalı kayıtlar kontrol ediliyor...")
        cursor.execute("SELECT id, created_at FROM progress_analysis")
        all_records = cursor.fetchall()
        
        fixed_count = 0
        for record_id, created_at in all_records:
            # Eğer created_at bir UUID gibi görünüyorsa (UUID uzunluğu 36 karakter)
            if created_at and len(str(created_at)) == 36 and '-' in str(created_at):
                # UUID olup olmadığını kontrol et
                if str(created_at).count('-') == 4:
                    print(f"   ⚠️  ID {record_id}: Hatalı created_at bulundu: {created_at}")
                    
                    # Şimdiki zamanı kullan
                    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
                    cursor.execute(
                        "UPDATE progress_analysis SET created_at = ? WHERE id = ?",
                        (now, record_id)
                    )
                    fixed_count += 1
                    print(f"   ✅ Düzeltildi: {now}")
        
        if fixed_count > 0:
            conn.commit()
            print(f"\n✅ {fixed_count} kayıt düzeltildi!")
        else:
            print("\n✅ Hatalı kayıt bulunamadı, tüm veriler temiz!")
        
        # Son durumu göster
        print("\n2. Güncel kayıtlar:")
        cursor.execute("SELECT id, date_range, created_at FROM progress_analysis ORDER BY id DESC LIMIT 5")
        records = cursor.fetchall()
        for rec in records:
            print(f"   ID {rec[0]}: {rec[1]} - {rec[2]}")
        
        print("\n" + "="*60)
        print("✅ İŞLEM TAMAMLANDI!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ HATA: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    fix_created_at()

