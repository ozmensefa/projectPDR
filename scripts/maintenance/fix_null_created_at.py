# -*- coding: utf-8 -*-
"""
NULL created_at değerlerini düzelt
"""
import sqlite3
from datetime import datetime

def fix_null_created_at():
    db_path = '/home/sefa4/projectPDR/instance/app.db'
    
    print("\n" + "="*60)
    print("NULL CREATED_AT DEĞERLERİ DÜZELTİLİYOR")
    print("="*60 + "\n")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # NULL created_at değerlerini bul
        print("1. NULL created_at değerleri kontrol ediliyor...")
        cursor.execute("""
            SELECT id, date_range 
            FROM progress_analysis 
            WHERE created_at IS NULL
        """)
        null_records = cursor.fetchall()
        
        if null_records:
            print(f"   ⚠️  {len(null_records)} kayıtta NULL created_at bulundu\n")
            
            # Her birini düzelt
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
            for record_id, date_range in null_records:
                cursor.execute("""
                    UPDATE progress_analysis 
                    SET created_at = ? 
                    WHERE id = ?
                """, (now, record_id))
                print(f"   ✅ ID {record_id} ({date_range}): {now}")
            
            conn.commit()
            print(f"\n✅ {len(null_records)} kayıt düzeltildi!")
        else:
            print("   ✅ NULL created_at değeri yok\n")
        
        # Tüm kayıtları göster
        print("2. Tüm progress_analysis kayıtları:")
        cursor.execute("""
            SELECT id, date_range, created_at 
            FROM progress_analysis 
            ORDER BY id
        """)
        all_records = cursor.fetchall()
        
        for rec in all_records:
            status = "✅" if rec[2] else "❌"
            print(f"   {status} ID {rec[0]}: {rec[1]} - {rec[2]}")
        
        print("\n" + "="*60)
        print("✅ İŞLEM TAMAMLANDI!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ HATA: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    fix_null_created_at()

