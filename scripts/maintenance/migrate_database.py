# -*- coding: utf-8 -*-
"""
Veritabanı Migration Script - Yeni Kolonları Ekler
Bu script mevcut veritabanına yeni eklenen kolonları ekler.
"""
import sqlite3
import os

def migrate_database():
    """Session, Notification ve ProgressAnalysis tablolarını güncelle"""
    
    db_paths = [
        'app.db',
        'instance/app.db'
    ]
    
    for db_path in db_paths:
        if not os.path.exists(db_path):
            print(f"❌ Veritabanı bulunamadı: {db_path}")
            continue
        
        print(f"\n{'='*60}")
        print(f"📊 Veritabanı güncelleniyor: {db_path}")
        print(f"{'='*60}\n")
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Session tablosuna yeni kolonlar ekle
            print("1️⃣ Session tablosu güncelleniyor...")
            
            try:
                cursor.execute("ALTER TABLE session ADD COLUMN analysis_status VARCHAR(20) DEFAULT 'pending'")
                print("   ✅ analysis_status kolonu eklendi")
            except sqlite3.OperationalError as e:
                if 'duplicate column name' in str(e).lower():
                    print("   ⏭️ analysis_status kolonu zaten mevcut")
                else:
                    raise e
            
            try:
                cursor.execute("ALTER TABLE session ADD COLUMN analysis_progress INTEGER DEFAULT 0")
                print("   ✅ analysis_progress kolonu eklendi")
            except sqlite3.OperationalError as e:
                if 'duplicate column name' in str(e).lower():
                    print("   ⏭️ analysis_progress kolonu zaten mevcut")
                else:
                    raise e
            
            try:
                cursor.execute("ALTER TABLE session ADD COLUMN task_id VARCHAR(100)")
                print("   ✅ task_id kolonu eklendi")
            except sqlite3.OperationalError as e:
                if 'duplicate column name' in str(e).lower():
                    print("   ⏭️ task_id kolonu zaten mevcut")
                else:
                    raise e
            
            # Notification tablosu oluştur
            print("\n2️⃣ Notification tablosu oluşturuluyor...")
            
            try:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS notification (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        counselor_id INTEGER NOT NULL,
                        title VARCHAR(200) NOT NULL,
                        message TEXT NOT NULL,
                        notification_type VARCHAR(50) DEFAULT 'info',
                        is_read BOOLEAN DEFAULT 0,
                        link VARCHAR(500),
                        related_session_id INTEGER,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (counselor_id) REFERENCES counselor(id),
                        FOREIGN KEY (related_session_id) REFERENCES session(id)
                    )
                """)
                print("   ✅ Notification tablosu oluşturuldu")
            except sqlite3.OperationalError as e:
                print(f"   ⏭️ Notification tablosu zaten mevcut: {e}")
            
            # Değişiklikleri kaydet
            conn.commit()
            
            # Tablo yapısını göster
            print("\n📋 Session tablosu yapısı:")
            cursor.execute("PRAGMA table_info(session)")
            columns = cursor.fetchall()
            for col in columns:
                print(f"   - {col[1]}: {col[2]}")
            
            print("\n📋 Notification tablosu yapısı:")
            cursor.execute("PRAGMA table_info(notification)")
            columns = cursor.fetchall()
            for col in columns:
                print(f"   - {col[1]}: {col[2]}")
            
            # ProgressAnalysis tablosuna yeni kolonlar ekle
            print("\n3️⃣ ProgressAnalysis tablosu güncelleniyor...")
            
            try:
                cursor.execute("ALTER TABLE progress_analysis ADD COLUMN analysis_status VARCHAR(20) DEFAULT 'pending'")
                print("   ✅ analysis_status kolonu eklendi")
            except sqlite3.OperationalError as e:
                if 'duplicate column name' in str(e).lower():
                    print("   ⏭️ analysis_status kolonu zaten mevcut")
                else:
                    raise e
            
            try:
                cursor.execute("ALTER TABLE progress_analysis ADD COLUMN analysis_progress INTEGER DEFAULT 0")
                print("   ✅ analysis_progress kolonu eklendi")
            except sqlite3.OperationalError as e:
                if 'duplicate column name' in str(e).lower():
                    print("   ⏭️ analysis_progress kolonu zaten mevcut")
                else:
                    raise e
            
            try:
                cursor.execute("ALTER TABLE progress_analysis ADD COLUMN task_id VARCHAR(100)")
                print("   ✅ task_id kolonu eklendi")
            except sqlite3.OperationalError as e:
                if 'duplicate column name' in str(e).lower():
                    print("   ⏭️ task_id kolonu zaten mevcut")
                else:
                    raise e
            
            # analysis_text kolonunu nullable yap (SQLite'da ALTER COLUMN doğrudan yapılamaz)
            try:
                # Mevcut verileri kontrol et
                cursor.execute("SELECT COUNT(*) FROM progress_analysis WHERE analysis_text IS NULL")
                null_count = cursor.fetchone()[0]
                print(f"   ℹ️ analysis_text NULL olan {null_count} kayıt mevcut")
            except Exception as e:
                print(f"   ⚠️ analysis_text kontrolü yapılamadı: {e}")
            
            # Mevcut session'ları güncelle
            print("\n4️⃣ Mevcut session kayıtları güncelleniyor...")
            cursor.execute("""
                UPDATE session 
                SET analysis_status = 'pending', 
                    analysis_progress = 0 
                WHERE analysis_status IS NULL
            """)
            updated_count = cursor.rowcount
            print(f"   ✅ {updated_count} session kaydı güncellendi")
            
            # Mevcut progress_analysis kayıtlarını güncelle
            print("\n5️⃣ Mevcut progress_analysis kayıtları güncelleniyor...")
            
            # analysis_text olan kayıtları completed yap
            cursor.execute("""
                UPDATE progress_analysis 
                SET analysis_status = 'completed', 
                    analysis_progress = 100 
                WHERE analysis_text IS NOT NULL 
                AND (analysis_status IS NULL OR analysis_status = 'pending')
            """)
            completed_count = cursor.rowcount
            
            # analysis_text olmayan kayıtları pending yap
            cursor.execute("""
                UPDATE progress_analysis 
                SET analysis_status = 'pending', 
                    analysis_progress = 0 
                WHERE analysis_text IS NULL 
                AND analysis_status IS NULL
            """)
            pending_count = cursor.rowcount
            
            print(f"   ✅ {completed_count} kayıt 'completed' olarak güncellendi")
            print(f"   ✅ {pending_count} kayıt 'pending' olarak güncellendi")
            
            conn.commit()
            
            # ProgressAnalysis tablo yapısını göster
            print("\n📋 ProgressAnalysis tablosu yapısı:")
            cursor.execute("PRAGMA table_info(progress_analysis)")
            columns = cursor.fetchall()
            for col in columns:
                print(f"   - {col[1]}: {col[2]}")
            
            conn.close()
            
            print(f"\n✅ {db_path} başarıyla güncellendi!")
            
        except Exception as e:
            print(f"\n❌ Hata: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*60}")
    print("🎉 Veritabanı migration tamamlandı!")
    print(f"{'='*60}\n")

if __name__ == '__main__':
    migrate_database()

