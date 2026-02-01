# -*- coding: utf-8 -*-
"""
Veritabanı tablosunu zorla düzelt
"""
import sqlite3
import os

def fix_database():
    db_path = '/home/sefa4/projectPDR/instance/app.db'
    
    print("\n" + "="*60)
    print("VERİTABANI TABLOSU ZORLA DÜZELTİLİYOR")
    print("="*60 + "\n")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. Mevcut yapıyı kontrol et
        cursor.execute("PRAGMA table_info(progress_analysis)")
        columns = cursor.fetchall()
        
        print("Mevcut tablo yapısı:")
        for col in columns:
            print(f"  {col[1]}: NOT NULL={col[3]}")
        
        # 2. Tüm verileri yedekle
        print("\n1. Veriler yedekleniyor...")
        cursor.execute("SELECT * FROM progress_analysis")
        all_data = cursor.fetchall()
        print(f"   ✅ {len(all_data)} kayıt yedeklendi")
        
        # 3. Tabloyu sil
        print("\n2. Eski tablo siliniyor...")
        cursor.execute("DROP TABLE IF EXISTS progress_analysis")
        conn.commit()
        print("   ✅ Tablo silindi")
        
        # 4. Yeni tabloyu doğru şekilde oluştur
        print("\n3. Yeni tablo oluşturuluyor (analysis_text NULLABLE)...")
        cursor.execute("""
            CREATE TABLE progress_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                counselor_id INTEGER NOT NULL,
                client_id INTEGER NOT NULL,
                start_session_id INTEGER NOT NULL,
                end_session_id INTEGER NOT NULL,
                analysis_text TEXT,
                sessions_analyzed INTEGER NOT NULL,
                date_range VARCHAR(100) NOT NULL,
                analysis_status VARCHAR(20) DEFAULT 'pending',
                analysis_progress INTEGER DEFAULT 0,
                task_id VARCHAR(100),
                created_at DATETIME,
                FOREIGN KEY (counselor_id) REFERENCES counselor(id),
                FOREIGN KEY (client_id) REFERENCES client(id),
                FOREIGN KEY (start_session_id) REFERENCES session(id),
                FOREIGN KEY (end_session_id) REFERENCES session(id)
            )
        """)
        conn.commit()
        print("   ✅ Yeni tablo oluşturuldu")
        
        # 5. Verileri geri yükle
        if all_data:
            print(f"\n4. {len(all_data)} kayıt geri yükleniyor...")
            cursor.executemany("""
                INSERT INTO progress_analysis 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, all_data)
            conn.commit()
            print(f"   ✅ {len(all_data)} kayıt geri yüklendi")
        
        # 6. Yeni yapıyı göster
        print("\n5. Yeni tablo yapısı:")
        cursor.execute("PRAGMA table_info(progress_analysis)")
        new_columns = cursor.fetchall()
        for col in new_columns:
            if col[1] == 'analysis_text':
                status = "✅ NULLABLE" if col[3] == 0 else "❌ NOT NULL"
                print(f"  {col[1]}: {status}")
        
        print("\n" + "="*60)
        print("✅ VERİTABANI BAŞARIYLA DÜZELTİLDİ!")
        print("="*60)
        print("\n⚠️  ÖNEMLİ: Flask ve Celery'yi yeniden başlatın!")
        
    except Exception as e:
        print(f"\n❌ HATA: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    fix_database()

