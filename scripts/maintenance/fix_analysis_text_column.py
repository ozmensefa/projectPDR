# -*- coding: utf-8 -*-
"""
ProgressAnalysis.analysis_text sütununu nullable yapmak için migration scripti
"""
from app import create_app, db
import sqlite3
import os

def fix_analysis_text_column():
    """analysis_text sütununu nullable yap"""
    app = create_app()
    
    with app.app_context():
        # Veritabanı dosyasının yolunu al
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        
        print(f"Veritabanı: {db_path}")
        print("\n" + "="*60)
        print("ANALYSIS_TEXT SÜTUNU DÜZELTİLİYOR")
        print("="*60 + "\n")
        
        # SQLite bağlantısı
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            # Mevcut tablo yapısını kontrol et
            cursor.execute("PRAGMA table_info(progress_analysis)")
            columns = cursor.fetchall()
            
            print("Mevcut sütunlar:")
            for col in columns:
                col_name = col[1]
                col_type = col[2]
                not_null = col[3]
                default_val = col[4]
                print(f"  - {col_name}: {col_type}, NOT NULL={not_null}, DEFAULT={default_val}")
            
            # analysis_text sütununun NOT NULL durumunu kontrol et
            analysis_text_col = [col for col in columns if col[1] == 'analysis_text']
            
            if analysis_text_col and analysis_text_col[0][3] == 1:  # NOT NULL = 1
                print("\n⚠️  analysis_text sütunu NOT NULL olarak tanımlı, düzeltiliyor...\n")
                
                # SQLite'da ALTER TABLE ile NOT NULL değiştirilemez
                # Yeni tablo oluşturup veri kopyalamamız gerekiyor
                
                # 1. Yedek tablo oluştur
                print("1. Yedek tablo oluşturuluyor...")
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS progress_analysis_backup AS 
                    SELECT * FROM progress_analysis
                """)
                print("   ✅ Yedek alındı")
                
                # 2. Eski tabloyu sil
                print("2. Eski tablo siliniyor...")
                cursor.execute("DROP TABLE progress_analysis")
                print("   ✅ Eski tablo silindi")
                
                # 3. Yeni tablo oluştur (analysis_text nullable olarak)
                print("3. Yeni tablo oluşturuluyor...")
                cursor.execute("""
                    CREATE TABLE progress_analysis (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        counselor_id INTEGER NOT NULL,
                        client_id INTEGER NOT NULL,
                        start_session_id INTEGER NOT NULL,
                        end_session_id INTEGER NOT NULL,
                        analysis_text TEXT,  -- NULLABLE!
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
                print("   ✅ Yeni tablo oluşturuldu")
                
                # 4. Verileri geri kopyala
                print("4. Veriler geri kopyalanıyor...")
                cursor.execute("""
                    INSERT INTO progress_analysis 
                    SELECT * FROM progress_analysis_backup
                """)
                row_count = cursor.rowcount
                print(f"   ✅ {row_count} kayıt kopyalandı")
                
                # 5. Yedek tabloyu sil
                print("5. Yedek tablo siliniyor...")
                cursor.execute("DROP TABLE progress_analysis_backup")
                print("   ✅ Yedek tablo silindi")
                
                # Değişiklikleri kaydet
                conn.commit()
                
                print("\n" + "="*60)
                print("✅ BAŞARILI!")
                print("="*60)
                print("\nYeni tablo yapısı:")
                
                cursor.execute("PRAGMA table_info(progress_analysis)")
                new_columns = cursor.fetchall()
                for col in new_columns:
                    col_name = col[1]
                    col_type = col[2]
                    not_null = col[3]
                    default_val = col[4]
                    if col_name == 'analysis_text':
                        status = "✅ NULLABLE" if not_null == 0 else "❌ NOT NULL"
                        print(f"  - {col_name}: {col_type}, {status}")
                
                print("\n🎉 analysis_text sütunu artık NULL değer kabul ediyor!")
                
            else:
                print("\n✅ analysis_text sütunu zaten nullable, düzeltmeye gerek yok!")
            
        except Exception as e:
            print(f"\n❌ Hata: {str(e)}")
            conn.rollback()
            raise
        finally:
            conn.close()

if __name__ == '__main__':
    fix_analysis_text_column()

