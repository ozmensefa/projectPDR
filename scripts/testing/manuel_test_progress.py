# -*- coding: utf-8 -*-
"""
Manuel İlerleyiş Analizi Test Scripti
Gerçek bir ilerleyiş analizi oluşturur ve izler
"""
from app import create_app, db
from app.models import Client, Session, ProgressAnalysis, Counselor
from app.tasks import analyze_progress
import time

def main():
    print("\n" + "="*60)
    print("MANUEL İLERLEYİŞ ANALİZİ TESTİ")
    print("="*60)
    
    app = create_app()
    with app.app_context():
        # İlk danışmanı al
        counselor = Counselor.query.first()
        if not counselor:
            print("❌ Danışman bulunamadı!")
            return
        
        print(f"\n✅ Danışman: {counselor.name} (ID: {counselor.id})")
        
        # En az 2 oturumu olan bir danışan bul
        clients = Client.query.filter_by(counselor_id=counselor.id).all()
        
        suitable_client = None
        for client in clients:
            sessions = Session.query.filter_by(client_id=client.id).order_by(Session.date.asc()).all()
            if len(sessions) >= 2:
                suitable_client = client
                break
        
        if not suitable_client:
            print("❌ En az 2 oturumu olan danışan bulunamadı!")
            return
        
        sessions = Session.query.filter_by(client_id=suitable_client.id).order_by(Session.date.asc()).all()
        
        print(f"\n✅ Test Danışanı: {suitable_client.name} (ID: {suitable_client.id})")
        print(f"   Toplam {len(sessions)} oturum mevcut")
        print(f"   İlk oturum: {sessions[0].title} - {sessions[0].date.strftime('%d.%m.%Y')}")
        print(f"   Son oturum: {sessions[-1].title} - {sessions[-1].date.strftime('%d.%m.%Y')}")
        
        # Tarih aralığını formatla
        date_range = f"{sessions[0].date.strftime('%d.%m.%Y')} - {sessions[-1].date.strftime('%d.%m.%Y')}"
        
        print(f"\n🚀 YENİ İLERLEYİŞ ANALİZİ OLUŞTURULUYOR...")
        print(f"   Tarih Aralığı: {date_range}")
        print(f"   Oturum Sayısı: {len(sessions)}")
        
        # ProgressAnalysis kaydı oluştur
        progress_analysis = ProgressAnalysis(
            counselor_id=counselor.id,
            client_id=suitable_client.id,
            start_session_id=sessions[0].id,
            end_session_id=sessions[-1].id,
            sessions_analyzed=len(sessions),
            date_range=date_range,
            analysis_status='pending',
            analysis_progress=0
        )
        
        db.session.add(progress_analysis)
        db.session.commit()
        
        print(f"✅ ProgressAnalysis kaydı oluşturuldu (ID: {progress_analysis.id})")
        
        # Celery task'ını başlat
        print(f"\n🎬 CELERY TASK BAŞLATILIYOR...")
        task = analyze_progress.apply_async(
            args=[progress_analysis.id, counselor.id],
            countdown=1
        )
        
        # Task ID'yi kaydet
        progress_analysis.task_id = task.id
        progress_analysis.analysis_status = 'processing'
        db.session.commit()
        
        print(f"✅ Celery task başlatıldı!")
        print(f"   Task ID: {task.id}")
        print(f"   Progress Analysis ID: {progress_analysis.id}")
        
        # İlerlemeyi izle
        print(f"\n📊 ANALİZ İLERLEMESİ İZLENİYOR...")
        print("   (Her 3 saniyede bir kontrol edilecek, CTRL+C ile durdurun)\n")
        
        try:
            last_progress = 0
            while True:
                time.sleep(3)
                
                # Veritabanından güncel durumu al
                db.session.refresh(progress_analysis)
                
                # Eğer ilerleme değiştiyse göster
                if progress_analysis.analysis_progress != last_progress:
                    print(f"   [{progress_analysis.analysis_status}] İlerleme: {progress_analysis.analysis_progress}%")
                    last_progress = progress_analysis.analysis_progress
                
                # Analiz tamamlandı mı?
                if progress_analysis.analysis_status == 'completed':
                    print(f"\n✅ ANALİZ TAMAMLANDI!")
                    print(f"   Süre: Yaklaşık {last_progress * 0.3} saniye")
                    print(f"   Sonuç uzunluğu: {len(progress_analysis.analysis_text or '')} karakter")
                    print(f"\n📄 Raporu görüntülemek için:")
                    print(f"   http://127.0.0.1:8000/view_progress_report/{progress_analysis.id}")
                    break
                elif progress_analysis.analysis_status == 'failed':
                    print(f"\n❌ ANALİZ BAŞARISIZ!")
                    print(f"   Hata: {progress_analysis.analysis_text}")
                    break
                    
        except KeyboardInterrupt:
            print(f"\n\n⚠️  İzleme durduruldu")
            print(f"   Analiz arka planda devam ediyor...")
            print(f"   Durumu kontrol etmek için:")
            print(f"   http://127.0.0.1:8000/view_progress_report/{progress_analysis.id}")

if __name__ == '__main__':
    main()

