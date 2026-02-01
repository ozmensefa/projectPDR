# -*- coding: utf-8 -*-
"""
Veritabanını yeniden oluştur
"""
from app import create_app, db
import os

def recreate_database():
    print("\n" + "="*60)
    print("VERİTABANI YENİDEN OLUŞTURULUYOR")
    print("="*60 + "\n")
    
    app = create_app()
    
    with app.app_context():
        try:
            # Instance klasörünü oluştur
            instance_path = os.path.join(os.getcwd(), 'instance')
            if not os.path.exists(instance_path):
                os.makedirs(instance_path)
                print(f"✅ Instance klasörü oluşturuldu: {instance_path}")
            else:
                print(f"✅ Instance klasörü mevcut: {instance_path}")
            
            # Veritabanı dosyasının yolunu göster
            db_path = os.path.join(instance_path, 'app.db')
            print(f"📁 Veritabanı yolu: {db_path}")
            
            # Tüm tabloları oluştur
            print("\n📊 Tablolar oluşturuluyor...")
            db.create_all()
            print("✅ Tüm tablolar başarıyla oluşturuldu!")
            
            # Tabloları listele
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            print(f"\n📋 Oluşturulan tablolar ({len(tables)} adet):")
            for table in tables:
                print(f"   - {table}")
            
            print("\n" + "="*60)
            print("✅ VERİTABANI HAZIR!")
            print("="*60)
            print("\nŞimdi Flask'ı başlatın:")
            print("  python3 run.py")
            
        except Exception as e:
            print(f"\n❌ HATA: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    recreate_database()

