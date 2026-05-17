# -*- coding: utf-8 -*-
"""
Celery ve İlerleyiş Analizi Test Scripti
"""
import sys
import os

print("="*70)
print("CELERY VE İLERLEYİŞ ANALİZİ TEST SCRIPTI")
print("="*70)

# 1. Redis Bağlantı Kontrolü
print("\n1️⃣ Redis Bağlantı Kontrolü...")
try:
    import redis
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    redis_client.ping()
    print("   ✅ Redis bağlantısı başarılı!")
    
    # Redis bilgileri
    info = redis_client.info()
    print(f"   📊 Redis Versiyonu: {info.get('redis_version', 'Bilinmiyor')}")
    print(f"   📊 Kullanılan Bellek: {info.get('used_memory_human', 'Bilinmiyor')}")
except ImportError:
    print("   ❌ redis paketi yüklü değil!")
    print("   💡 Çözüm: pip install redis")
    sys.exit(1)
except Exception as e:
    print(f"   ❌ Redis bağlantı hatası: {e}")
    print("   💡 Çözüm: Redis servisini başlatın: redis-server")
    sys.exit(1)

# 2. Celery Konfigürasyon Kontrolü
print("\n2️⃣ Celery Konfigürasyon Kontrolü...")
try:
    from app import create_app
    from app.celery_config import make_celery
    
    app = create_app()
    celery = make_celery(app)
    
    print("   ✅ Celery konfigürasyonu başarılı!")
    print(f"   📊 Broker: {celery.conf.broker_url}")
    print(f"   📊 Backend: {celery.conf.result_backend}")
    print(f"   📊 Task Modules: {celery.conf.include}")
except Exception as e:
    print(f"   ❌ Celery konfigürasyon hatası: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 3. Task Import Kontrolü
print("\n3️⃣ Task Import Kontrolü...")
try:
    from app.tasks import analyze_video, analyze_progress
    print("   ✅ analyze_video task'ı başarıyla import edildi")
    print(f"   📊 Task Name: {analyze_video.name}")
    print("   ✅ analyze_progress task'ı başarıyla import edildi")
    print(f"   📊 Task Name: {analyze_progress.name}")
except Exception as e:
    print(f"   ❌ Task import hatası: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 4. Celery Worker Kontrolü
print("\n4️⃣ Celery Worker Kontrolü...")
try:
    # Celery inspect ile aktif worker'ları kontrol et
    inspect = celery.control.inspect()
    active_workers = inspect.active()
    
    if active_workers:
        print(f"   ✅ {len(active_workers)} aktif worker bulundu!")
        for worker_name, tasks in active_workers.items():
            print(f"   👷 Worker: {worker_name}")
            if tasks:
                print(f"      🔧 Çalışan task sayısı: {len(tasks)}")
            else:
                print(f"      💤 Boşta")
    else:
        print("   ⚠️  Aktif worker bulunamadı!")
        print("   💡 Çözüm: Celery worker'ı başlatın:")
        print("      celery -A celery_worker.celery worker --loglevel=info --pool=solo")
except Exception as e:
    print(f"   ⚠️  Worker kontrolü yapılamadı: {e}")
    print("   💡 Worker muhtemelen çalışmıyor")

# 5. Veritabanı Kontrolü
print("\n5️⃣ Veritabanı ve Model Kontrolü...")
try:
    with app.app_context():
        from app.models import ProgressAnalysis, Session, Client, Counselor
        from app import db
        
        # Tablo kontrolü
        print("   ✅ Tüm modeller başarıyla import edildi")
        
        # Örnek veri kontrolü
        progress_count = ProgressAnalysis.query.count()
        session_count = Session.query.count()
        client_count = Client.query.count()
        counselor_count = Counselor.query.count()
        
        print(f"   📊 ProgressAnalysis kayıt sayısı: {progress_count}")
        print(f"   📊 Session kayıt sayısı: {session_count}")
        print(f"   📊 Client kayıt sayısı: {client_count}")
        print(f"   📊 Counselor kayıt sayısı: {counselor_count}")
        
        if progress_count > 0:
            # Son ProgressAnalysis kaydını kontrol et
            last_analysis = ProgressAnalysis.query.order_by(ProgressAnalysis.created_at.desc()).first()
            print(f"\n   📋 Son İlerleyiş Analizi:")
            print(f"      ID: {last_analysis.id}")
            print(f"      Danışan: {last_analysis.client.name}")
            print(f"      Durum: {last_analysis.analysis_status}")
            print(f"      İlerleme: {last_analysis.analysis_progress}%")
            print(f"      Tarih Aralığı: {last_analysis.date_range}")
            if last_analysis.task_id:
                print(f"      Task ID: {last_analysis.task_id}")
        
except Exception as e:
    print(f"   ❌ Veritabanı kontrolü hatası: {e}")
    import traceback
    traceback.print_exc()

# 6. Gemini API Kontrolü
print("\n6️⃣ Gemini API Kontrolü...")
try:
    from app.config import Config
    
    # Oturum API Key kontrolü
    if Config.GEMINI_API_KEY_SESSION:
        key_preview = Config.GEMINI_API_KEY_SESSION[:10] + "..." + Config.GEMINI_API_KEY_SESSION[-4:]
        print(f"   ✅ Gemini Oturum API Key bulundu: {key_preview}")
        
        is_valid, message = Config.validate_gemini_api_key('session')
        if is_valid:
            print(f"   ✅ Oturum API Key formatı geçerli")
        else:
            print(f"   ⚠️  Oturum API Key uyarısı: {message}")
    else:
        print("   ❌ Gemini Oturum API Key bulunamadı!")
        print("   💡 .env dosyasında GEMINI_API_KEY_SESSION ayarlayın")
    
    # İlerleyiş API Key kontrolü
    if Config.GEMINI_API_KEY_PROGRESS:
        key_preview = Config.GEMINI_API_KEY_PROGRESS[:10] + "..." + Config.GEMINI_API_KEY_PROGRESS[-4:]
        print(f"   ✅ Gemini İlerleyiş API Key bulundu: {key_preview}")
        
        is_valid, message = Config.validate_gemini_api_key('progress')
        if is_valid:
            print(f"   ✅ İlerleyiş API Key formatı geçerli")
        else:
            print(f"   ⚠️  İlerleyiş API Key uyarısı: {message}")
    else:
        print("   ❌ Gemini İlerleyiş API Key bulunamadı!")
        print("   💡 .env dosyasında GEMINI_API_KEY_PROGRESS ayarlayın")
except Exception as e:
    print(f"   ❌ API kontrolü hatası: {e}")

# 7. Test Task Gönderimi (Opsiyonel)
print("\n7️⃣ Test Task Gönderimi...")
print("   ⏭️  Test task gönderimi atlandı (gerçek analiz yapmamak için)")
print("   💡 Manuel test için:")
print("      python")
print("      >>> from app import create_app")
print("      >>> from app.tasks import analyze_progress")
print("      >>> app = create_app()")
print("      >>> with app.app_context():")
print("      ...     task = analyze_progress.apply_async(args=[1, 1])")
print("      ...     print(f'Task ID: {task.id}')")

print("\n" + "="*70)
print("TEST SONUCU")
print("="*70)
print("✅ Temel kontroller tamamlandı!")
print("\n💡 Celery worker'ı başlatmak için:")
print("   celery -A celery_worker.celery worker --loglevel=info --pool=solo")
print("\n💡 Flower (Celery monitoring) başlatmak için:")
print("   celery -A celery_worker.celery flower --port=5555")
print("="*70 + "\n")

