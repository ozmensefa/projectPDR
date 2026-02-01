# -*- coding: utf-8 -*-
"""
İlerleyiş Analizi Hızlı Düzeltme Scripti
Bu script ilerleyiş analizi ile ilgili yaygın sorunları otomatik düzeltir
"""
from app import create_app, db
from app.models import ProgressAnalysis
import sys

def fix_database_schema():
    """Veritabanı şemasını düzelt"""
    print("\n" + "="*60)
    print("1. VERİTABANI ŞEMASI DÜZELTİLİYOR")
    print("="*60)
    
    app = create_app()
    with app.app_context():
        try:
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'progress_analysis' not in tables:
                print("⚠️  ProgressAnalysis tablosu yok, oluşturuluyor...")
                db.create_all()
                print("✅ ProgressAnalysis tablosu oluşturuldu")
            else:
                print("✅ ProgressAnalysis tablosu zaten mevcut")
                
                # Sütunları kontrol et ve eksikleri ekle
                columns = [col['name'] for col in inspector.get_columns('progress_analysis')]
                
                # Gerekli sütunlar
                required_columns = {
                    'analysis_status': "VARCHAR(20) DEFAULT 'pending'",
                    'analysis_progress': "INTEGER DEFAULT 0",
                    'task_id': "VARCHAR(100)",
                }
                
                # Eksik sütunları tespit et
                missing_columns = [col for col in required_columns.keys() if col not in columns]
                
                if missing_columns:
                    print(f"⚠️  Eksik sütunlar bulundu: {', '.join(missing_columns)}")
                    print("   Migration script çalıştırılıyor...")
                    
                    # SQLite için ALTER TABLE
                    for col_name in missing_columns:
                        col_def = required_columns[col_name]
                        try:
                            db.session.execute(
                                f"ALTER TABLE progress_analysis ADD COLUMN {col_name} {col_def}"
                            )
                            print(f"✅ '{col_name}' sütunu eklendi")
                        except Exception as e:
                            print(f"⚠️  '{col_name}' eklenirken hata (zaten var olabilir): {str(e)}")
                    
                    db.session.commit()
                    print("✅ Veritabanı şeması güncellendi")
                else:
                    print("✅ Tüm sütunlar mevcut")
            
            return True
            
        except Exception as e:
            print(f"❌ Veritabanı düzeltme hatası: {str(e)}")
            db.session.rollback()
            return False

def fix_stuck_analyses():
    """Takılı kalmış analizleri düzelt"""
    print("\n" + "="*60)
    print("2. TAKILI KALAN ANALİZLER DÜZELTİLİYOR")
    print("="*60)
    
    app = create_app()
    with app.app_context():
        try:
            # 'processing' durumunda olan ve 1 saatten uzun süredir bekleyen analizleri bul
            from datetime import datetime, timedelta
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            
            stuck_analyses = ProgressAnalysis.query.filter(
                ProgressAnalysis.analysis_status == 'processing',
                ProgressAnalysis.created_at < one_hour_ago
            ).all()
            
            if stuck_analyses:
                print(f"⚠️  {len(stuck_analyses)} takılı kalmış analiz bulundu, sıfırlanıyor...")
                for analysis in stuck_analyses:
                    analysis.analysis_status = 'failed'
                    analysis.analysis_progress = 0
                    analysis.analysis_text = "Analiz zaman aşımına uğradı. Lütfen tekrar deneyin."
                    print(f"   - ID: {analysis.id} ({analysis.date_range}) -> failed")
                
                db.session.commit()
                print(f"✅ {len(stuck_analyses)} analiz sıfırlandı")
            else:
                print("✅ Takılı kalmış analiz yok")
            
            return True
            
        except Exception as e:
            print(f"❌ Takılı analiz düzeltme hatası: {str(e)}")
            db.session.rollback()
            return False

def check_celery_tasks():
    """Celery task'larını kontrol et"""
    print("\n" + "="*60)
    print("3. CELERY TASK KONTROLÜ")
    print("="*60)
    
    try:
        from app.celery_config import celery
        
        # Inspect objesi oluştur
        inspect = celery.control.inspect()
        
        # Aktif worker'ları kontrol et
        active_workers = inspect.active()
        
        if not active_workers:
            print("❌ Aktif Celery worker bulunamadı!")
            print("\n   ÇÖZÜM: Yeni bir terminal açın ve şu komutu çalıştırın:")
            print("   cd /home/sefa4/projectPDR")
            print("   source venv/bin/activate")
            print("   celery -A app.celery_config.celery worker --loglevel=info -E")
            return False
        
        print(f"✅ {len(active_workers)} aktif worker bulundu")
        
        # Registered tasks'leri kontrol et
        registered = inspect.registered()
        has_progress_task = False
        
        if registered:
            for worker_name, tasks in registered.items():
                if 'app.tasks.analyze_progress' in tasks:
                    has_progress_task = True
                    print(f"✅ 'analyze_progress' task'ı {worker_name} worker'ında kayıtlı")
        
        if not has_progress_task:
            print("⚠️  'analyze_progress' task'ı kayıtlı değil!")
            print("   Worker'ı yeniden başlatın")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Celery kontrolü başarısız: {str(e)}")
        return False

def test_progress_analysis():
    """İlerleyiş analizini test et"""
    print("\n" + "="*60)
    print("4. İLERLEYİŞ ANALİZİ TEST EDİLİYOR")
    print("="*60)
    
    app = create_app()
    with app.app_context():
        try:
            from app.models import Client, Session
            
            # Test için uygun bir client bul
            clients = Client.query.all()
            
            if not clients:
                print("⚠️  Test için danışan bulunamadı")
                print("   Önce sisteme danışan eklemeniz gerekiyor")
                return False
            
            for client in clients:
                sessions = Session.query.filter_by(client_id=client.id).order_by(Session.date.asc()).all()
                
                if len(sessions) >= 2:
                    print(f"✅ Test için uygun danışan bulundu: {client.name}")
                    print(f"   - {len(sessions)} oturum mevcut")
                    print(f"   - İlk oturum: {sessions[0].title} ({sessions[0].date.strftime('%d.%m.%Y')})")
                    print(f"   - Son oturum: {sessions[-1].title} ({sessions[-1].date.strftime('%d.%m.%Y')})")
                    print(f"\n   İlerleyiş analizi oluşturmak için:")
                    print(f"   http://127.0.0.1:8000/progress_analysis/{client.id}")
                    return True
            
            print("⚠️  İlerleyiş analizi için yeterli oturum yok (en az 2 gerekli)")
            return False
            
        except Exception as e:
            print(f"❌ Test hatası: {str(e)}")
            return False

def main():
    """Ana düzeltme fonksiyonu"""
    print("\n" + "="*60)
    print("İLERLEYİŞ ANALİZİ DÜZELTME SCRIPTI")
    print("="*60)
    
    results = {
        'Veritabanı Şeması': fix_database_schema(),
        'Takılı Analizler': fix_stuck_analyses(),
        'Celery Task': check_celery_tasks(),
        'Test Hazırlığı': test_progress_analysis(),
    }
    
    print("\n" + "="*60)
    print("DÜZELTME SONUÇLARI")
    print("="*60)
    
    for fix_name, result in results.items():
        status = "✅ BAŞARILI" if result else "❌ BAŞARISIZ"
        print(f"{fix_name}: {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "="*60)
    if all_passed:
        print("🎉 TÜM DÜZELTMELER TAMAMLANDI!")
        print("İlerleyiş analizi sistemi kullanıma hazır.")
    else:
        print("⚠️  BAZI DÜZELTMELER BAŞARISIZ OLDU")
        print("Lütfen yukarıdaki mesajları kontrol edin.")
        
        # En yaygın sorunlar için çözümler
        print("\n📋 YAYGN SORUNLAR VE ÇÖZÜMLER:")
        print("\n1. Celery Worker Çalışmıyor:")
        print("   Terminal 1: redis-server --port 6380")
        print("   Terminal 2: cd /home/sefa4/projectPDR && source venv/bin/activate")
        print("              celery -A app.celery_config.celery worker --loglevel=info -E")
        print("   Terminal 3: cd /home/sefa4/projectPDR && source venv/bin/activate")
        print("              python3 run.py")
        
        print("\n2. Veritabanı Sorunları:")
        print("   python3 migrate_database.py")
        
        print("\n3. Redis Bağlantı Hatası:")
        print("   sudo systemctl start redis-server")
        print("   redis-cli -p 6380 ping")
    
    print("="*60 + "\n")
    
    return 0 if all_passed else 1

if __name__ == '__main__':
    sys.exit(main())

