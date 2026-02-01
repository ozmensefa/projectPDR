# -*- coding: utf-8 -*-
"""
İlerleyiş Analizi Sistem Test Scripti
Bu script ilerleyiş analizi sisteminin tüm bileşenlerini test eder
"""
from app import create_app, db
from app.models import ProgressAnalysis, Session, Client, Counselor
from app.tasks import analyze_progress
import sys

def test_database_model():
    """Veritabanı modelini test et"""
    print("\n" + "="*60)
    print("1. VERİTABANI MODELİ TESTİ")
    print("="*60)
    
    app = create_app()
    with app.app_context():
        try:
            # ProgressAnalysis tablosunun var olup olmadığını kontrol et
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'progress_analysis' in tables:
                print("✅ ProgressAnalysis tablosu mevcut")
                
                # Sütunları kontrol et
                columns = [col['name'] for col in inspector.get_columns('progress_analysis')]
                required_columns = [
                    'id', 'counselor_id', 'client_id', 'start_session_id', 
                    'end_session_id', 'analysis_text', 'sessions_analyzed',
                    'date_range', 'analysis_status', 'analysis_progress',
                    'task_id', 'created_at'
                ]
                
                missing_columns = [col for col in required_columns if col not in columns]
                if missing_columns:
                    print(f"⚠️  Eksik sütunlar: {', '.join(missing_columns)}")
                    print("   Migration çalıştırmanız gerekebilir: python migrate_database.py")
                    return False
                else:
                    print("✅ Tüm gerekli sütunlar mevcut")
                    
                # Kayıt sayısını göster
                count = db.session.query(ProgressAnalysis).count()
                print(f"📊 Toplam {count} ilerleyiş analizi kaydı bulundu")
                return True
            else:
                print("❌ ProgressAnalysis tablosu bulunamadı!")
                print("   Migration çalıştırın: python migrate_database.py")
                return False
                
        except Exception as e:
            print(f"❌ Veritabanı testi başarısız: {str(e)}")
            return False

def test_redis_connection():
    """Redis bağlantısını test et"""
    print("\n" + "="*60)
    print("2. REDIS BAĞLANTI TESTİ")
    print("="*60)
    
    try:
        import redis
        r = redis.Redis(host='localhost', port=6380, db=0)
        r.ping()
        print("✅ Redis bağlantısı başarılı (localhost:6380)")
        
        # Celery task sayısını kontrol et
        celery_keys = r.keys('celery*')
        print(f"📊 Redis'te {len(celery_keys)} Celery anahtarı bulundu")
        return True
        
    except redis.ConnectionError:
        print("❌ Redis'e bağlanılamadı!")
        print("   Redis'i başlatın: redis-server --port 6380")
        return False
    except Exception as e:
        print(f"❌ Redis testi başarısız: {str(e)}")
        return False

def test_celery_worker():
    """Celery worker'ın çalışıp çalışmadığını test et"""
    print("\n" + "="*60)
    print("3. CELERY WORKER TESTİ")
    print("="*60)
    
    try:
        from celery import Celery
        from app.celery_config import celery
        
        # Aktif worker'ları kontrol et
        inspect = celery.control.inspect()
        active_workers = inspect.active()
        
        if active_workers and len(active_workers) > 0:
            print(f"✅ {len(active_workers)} aktif Celery worker bulundu:")
            for worker_name in active_workers.keys():
                print(f"   - {worker_name}")
                
            # Registered tasks'leri kontrol et
            registered = inspect.registered()
            if registered:
                for worker_name, tasks in registered.items():
                    if 'app.tasks.analyze_progress' in tasks:
                        print("✅ 'analyze_progress' task'ı kayıtlı")
                    else:
                        print("⚠️  'analyze_progress' task'ı kayıtlı değil")
                        print("   Worker'ı yeniden başlatın")
            return True
        else:
            print("❌ Aktif Celery worker bulunamadı!")
            print("   Worker'ı başlatın: celery -A app.celery_config.celery worker --loglevel=info -E")
            return False
            
    except Exception as e:
        print(f"❌ Celery worker testi başarısız: {str(e)}")
        return False

def test_ai_service():
    """AI Service'i test et"""
    print("\n" + "="*60)
    print("4. AI SERVICE TESTİ")
    print("="*60)
    
    try:
        from app.services.ai_service import AIService
        from app.config import Config
        
        # API key kontrolü
        is_valid, message = Config.validate_gemini_api_key()
        if is_valid:
            print(f"✅ Gemini API Key geçerli: {Config.GEMINI_API_KEY[:10]}...")
        else:
            print(f"⚠️  Gemini API Key sorunu: {message}")
        
        # AIService başlatmayı dene
        ai_service = AIService()
        print("✅ AI Service başarıyla başlatıldı")
        
        # analyze_progress metodunun varlığını kontrol et
        if hasattr(ai_service, 'analyze_progress'):
            print("✅ 'analyze_progress' metodu mevcut")
            return True
        else:
            print("❌ 'analyze_progress' metodu bulunamadı!")
            return False
            
    except Exception as e:
        print(f"❌ AI Service testi başarısız: {str(e)}")
        return False

def test_routes():
    """Route'ları test et"""
    print("\n" + "="*60)
    print("5. ROUTE TESTİ")
    print("="*60)
    
    app = create_app()
    
    required_routes = [
        ('main.progress_analysis', 'GET'),
        ('main.generate_progress_report', 'POST'),
        ('main.view_progress_report', 'GET'),
        ('main.check_progress_analysis_status', 'GET'),
    ]
    
    all_routes_ok = True
    with app.app_context():
        for route_name, method in required_routes:
            try:
                # Route'un var olup olmadığını kontrol et
                from flask import url_for
                # Test endpoint'i oluştur (parametrelerle)
                if 'client_id' in route_name or 'progress' in route_name:
                    url = url_for(route_name, client_id=1, _external=False)
                elif 'report_id' in route_name:
                    url = url_for(route_name, report_id=1, _external=False)
                elif 'progress_analysis_id' in route_name:
                    url = url_for(route_name, progress_analysis_id=1, _external=False)
                else:
                    url = url_for(route_name, _external=False)
                    
                print(f"✅ {route_name} ({method}): {url}")
            except Exception as e:
                print(f"❌ {route_name} ({method}): Bulunamadı - {str(e)}")
                all_routes_ok = False
    
    return all_routes_ok

def test_sample_data():
    """Örnek veri kontrolü"""
    print("\n" + "="*60)
    print("6. ÖRNEK VERİ KONTROLÜ")
    print("="*60)
    
    app = create_app()
    with app.app_context():
        try:
            counselor_count = db.session.query(Counselor).count()
            client_count = db.session.query(Client).count()
            session_count = db.session.query(Session).count()
            progress_count = db.session.query(ProgressAnalysis).count()
            
            print(f"📊 Veritabanı İstatistikleri:")
            print(f"   - Danışman sayısı: {counselor_count}")
            print(f"   - Danışan sayısı: {client_count}")
            print(f"   - Oturum sayısı: {session_count}")
            print(f"   - İlerleyiş analizi sayısı: {progress_count}")
            
            if client_count == 0:
                print("\n⚠️  Henüz danışan kaydı yok. Test için danışan eklemeniz gerekir.")
            elif session_count < 2:
                print("\n⚠️  İlerleyiş analizi için en az 2 oturum gerekir.")
            else:
                print("\n✅ Yeterli test verisi mevcut")
                
            # En son ilerleyiş analizini göster
            if progress_count > 0:
                latest = db.session.query(ProgressAnalysis).order_by(
                    ProgressAnalysis.created_at.desc()
                ).first()
                print(f"\n📋 Son İlerleyiş Analizi:")
                print(f"   - ID: {latest.id}")
                print(f"   - Durum: {latest.analysis_status}")
                print(f"   - İlerleme: {latest.analysis_progress}%")
                print(f"   - Tarih Aralığı: {latest.date_range}")
                print(f"   - Task ID: {latest.task_id}")
                
            return True
            
        except Exception as e:
            print(f"❌ Örnek veri kontrolü başarısız: {str(e)}")
            return False

def main():
    """Ana test fonksiyonu"""
    print("\n" + "="*60)
    print("İLERLEYİŞ ANALİZİ SİSTEM TESTİ")
    print("="*60)
    
    results = {
        'Veritabanı Modeli': test_database_model(),
        'Redis Bağlantısı': test_redis_connection(),
        'Celery Worker': test_celery_worker(),
        'AI Service': test_ai_service(),
        'Route\'lar': test_routes(),
        'Örnek Veri': test_sample_data(),
    }
    
    print("\n" + "="*60)
    print("TEST SONUÇLARI")
    print("="*60)
    
    for test_name, result in results.items():
        status = "✅ BAŞARILI" if result else "❌ BAŞARISIZ"
        print(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "="*60)
    if all_passed:
        print("🎉 TÜM TESTLER BAŞARILI!")
        print("İlerleyiş analizi sistemi çalışmaya hazır.")
    else:
        print("⚠️  BAZI TESTLER BAŞARISIZ OLDU")
        print("Lütfen yukarıdaki hata mesajlarını kontrol edin.")
    print("="*60 + "\n")
    
    return 0 if all_passed else 1

if __name__ == '__main__':
    sys.exit(main())

