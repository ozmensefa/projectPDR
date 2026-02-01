# -*- coding: utf-8 -*-
"""
İlerleyiş Analizi Debug Scripti
Bu script mevcut progress analysis kayıtlarını kontrol eder ve sorunları tespit eder
"""
from app import create_app, db
from app.models import ProgressAnalysis, Session, Client, Counselor, AIAnalysis
import json

app = create_app()

print("="*70)
print("İLERLEYİŞ ANALİZİ DEBUG SCRIPTI")
print("="*70)

with app.app_context():
    # Tüm ProgressAnalysis kayıtlarını al
    all_progress = ProgressAnalysis.query.order_by(ProgressAnalysis.created_at.desc()).all()
    
    print(f"\n📊 Toplam İlerleyiş Analizi Sayısı: {len(all_progress)}")
    
    if not all_progress:
        print("\n⚠️  Henüz hiç ilerleyiş analizi oluşturulmamış!")
        print("\n💡 Yeni bir ilerleyiş analizi oluşturmak için:")
        print("   1. Web arayüzünden bir danışan seçin")
        print("   2. 'İlerleyiş Analizi' butonuna tıklayın")
        print("   3. Başlangıç ve bitiş oturumlarını seçin")
        print("   4. 'İlerleyiş Analizi Oluştur' butonuna tıklayın")
    else:
        print("\n" + "="*70)
        print("MEVCUT İLERLEYİŞ ANALİZLERİ")
        print("="*70)
        
        for idx, progress in enumerate(all_progress, 1):
            print(f"\n{idx}. İLERLEYİŞ ANALİZİ")
            print("-" * 70)
            print(f"   🆔 ID: {progress.id}")
            print(f"   👤 Danışan: {progress.client.name} (ID: {progress.client_id})")
            print(f"   👨‍⚕️ Danışman: {progress.counselor.name} (ID: {progress.counselor_id})")
            print(f"   📅 Tarih Aralığı: {progress.date_range}")
            print(f"   📊 Analiz Edilen Oturum: {progress.sessions_analyzed}")
            print(f"   🔄 Durum: {progress.analysis_status}")
            print(f"   📈 İlerleme: {progress.analysis_progress}%")
            print(f"   🕐 Oluşturulma: {progress.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            
            if progress.task_id:
                print(f"   🎯 Task ID: {progress.task_id}")
            else:
                print(f"   ⚠️  Task ID yok!")
            
            # Başlangıç ve bitiş oturumları
            print(f"\n   📋 Başlangıç Oturumu:")
            print(f"      - ID: {progress.start_session.id}")
            print(f"      - Başlık: {progress.start_session.title}")
            print(f"      - Tarih: {progress.start_session.date.strftime('%Y-%m-%d %H:%M:%S')}")
            
            print(f"\n   📋 Bitiş Oturumu:")
            print(f"      - ID: {progress.end_session.id}")
            print(f"      - Başlık: {progress.end_session.title}")
            print(f"      - Tarih: {progress.end_session.date.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Aralıktaki oturumları kontrol et
            sessions_in_range = Session.query.filter(
                Session.client_id == progress.client_id,
                Session.date >= progress.start_session.date,
                Session.date <= progress.end_session.date
            ).order_by(Session.date.asc()).all()
            
            print(f"\n   📊 Aralıktaki Oturum Sayısı: {len(sessions_in_range)}")
            
            # Analiz sonucu kontrolü
            if progress.analysis_text:
                text_length = len(progress.analysis_text)
                text_preview = progress.analysis_text[:100] + "..." if text_length > 100 else progress.analysis_text
                print(f"\n   📝 Analiz Metni:")
                print(f"      - Uzunluk: {text_length} karakter")
                print(f"      - Önizleme: {text_preview}")
            else:
                print(f"\n   ⚠️  Analiz metni yok!")
            
            # Durum kontrolü
            if progress.analysis_status == 'pending':
                print(f"\n   ⚠️  UYARI: Analiz 'pending' durumunda!")
                print(f"      - Celery worker çalışıyor mu kontrol edin")
                print(f"      - Task başlatıldı mı kontrol edin")
            elif progress.analysis_status == 'processing':
                print(f"\n   🔄 Analiz işleniyor...")
                print(f"      - İlerleme: {progress.analysis_progress}%")
                if progress.task_id:
                    print(f"      - Task ID ile durumu kontrol edebilirsiniz")
            elif progress.analysis_status == 'failed':
                print(f"\n   ❌ Analiz başarısız!")
                if progress.analysis_text:
                    print(f"      - Hata mesajı: {progress.analysis_text}")
            elif progress.analysis_status == 'completed':
                print(f"\n   ✅ Analiz başarıyla tamamlandı!")
            
            # Her oturumun AI analizini kontrol et
            print(f"\n   🔍 Oturum Analizleri Kontrolü:")
            for i, session in enumerate(sessions_in_range, 1):
                ai_analysis = AIAnalysis.query.filter_by(
                    session_id=session.id,
                    user_id=progress.counselor_id
                ).first()
                
                has_ai = "✅" if ai_analysis else "❌"
                has_results = "✅" if session.analysis_results else "❌"
                
                print(f"      {i}. {session.title} ({session.date.strftime('%d.%m.%Y')})")
                print(f"         AI Analizi: {has_ai} | Oturum Sonuçları: {has_results}")
    
    # Sorun tespiti
    print("\n" + "="*70)
    print("SORUN TESPİTİ")
    print("="*70)
    
    pending_analyses = ProgressAnalysis.query.filter_by(analysis_status='pending').count()
    processing_analyses = ProgressAnalysis.query.filter_by(analysis_status='processing').count()
    failed_analyses = ProgressAnalysis.query.filter_by(analysis_status='failed').count()
    completed_analyses = ProgressAnalysis.query.filter_by(analysis_status='completed').count()
    
    print(f"\n📊 Durum Özeti:")
    print(f"   ⏳ Bekleyen (pending): {pending_analyses}")
    print(f"   🔄 İşleniyor (processing): {processing_analyses}")
    print(f"   ❌ Başarısız (failed): {failed_analyses}")
    print(f"   ✅ Tamamlandı (completed): {completed_analyses}")
    
    if pending_analyses > 0:
        print(f"\n⚠️  {pending_analyses} adet bekleyen analiz var!")
        print("   Olası sorunlar:")
        print("   1. Celery worker çalışmıyor")
        print("   2. Redis servisi çalışmıyor")
        print("   3. Task başlatılamadı")
        print("\n   Çözüm:")
        print("   - Redis'i başlatın: redis-server")
        print("   - Celery worker'ı başlatın: celery -A celery_worker.celery worker --loglevel=info --pool=solo")
    
    if processing_analyses > 0:
        print(f"\n🔄 {processing_analyses} adet işlenen analiz var!")
        print("   - Bu analizler arka planda işleniyor")
        print("   - Worker loglarını kontrol edin")
    
    if failed_analyses > 0:
        print(f"\n❌ {failed_analyses} adet başarısız analiz var!")
        failed = ProgressAnalysis.query.filter_by(analysis_status='failed').all()
        for f in failed:
            print(f"   - ID {f.id}: {f.client.name} - {f.date_range}")
            if f.analysis_text:
                print(f"     Hata: {f.analysis_text[:100]}")

print("\n" + "="*70)
print("✅ Debug kontrolü tamamlandı!")
print("="*70 + "\n")

