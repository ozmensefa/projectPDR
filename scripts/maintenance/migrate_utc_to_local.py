# -*- coding: utf-8 -*-
"""
Veritabanındaki tüm UTC tarihlerini local time'a (UTC+3) çevir
"""
from app import create_app, db
from app.models import Counselor, Client, Session, AIAnalysis, ProgressAnalysis, Notification
from datetime import timedelta

def migrate_utc_to_local():
    print("\n" + "="*60)
    print("UTC → LOCAL TIME MİGRASYONU")
    print("="*60 + "\n")
    
    app = create_app()
    with app.app_context():
        try:
            total_updated = 0
            
            # 1. Counselor
            print("1. Counselor kayıtları güncelleniyor...")
            counselors = Counselor.query.all()
            for c in counselors:
                if c.created_at:
                    c.created_at = c.created_at + timedelta(hours=3)
            count = len(counselors)
            print(f"   ✅ {count} counselor güncellendi")
            total_updated += count
            
            # 2. Client
            print("\n2. Client kayıtları güncelleniyor...")
            clients = Client.query.all()
            for c in clients:
                if c.created_at:
                    c.created_at = c.created_at + timedelta(hours=3)
            count = len(clients)
            print(f"   ✅ {count} client güncellendi")
            total_updated += count
            
            # 3. Session
            print("\n3. Session kayıtları güncelleniyor...")
            sessions = Session.query.all()
            for s in sessions:
                if s.date:
                    s.date = s.date + timedelta(hours=3)
            count = len(sessions)
            print(f"   ✅ {count} session güncellendi")
            total_updated += count
            
            # 4. AIAnalysis
            print("\n4. AIAnalysis kayıtları güncelleniyor...")
            ai_analyses = AIAnalysis.query.all()
            for a in ai_analyses:
                if a.created_at:
                    a.created_at = a.created_at + timedelta(hours=3)
            count = len(ai_analyses)
            print(f"   ✅ {count} AI analysis güncellendi")
            total_updated += count
            
            # 5. ProgressAnalysis
            print("\n5. ProgressAnalysis kayıtları güncelleniyor...")
            progress_analyses = ProgressAnalysis.query.all()
            for p in progress_analyses:
                if p.created_at:
                    p.created_at = p.created_at + timedelta(hours=3)
            count = len(progress_analyses)
            print(f"   ✅ {count} progress analysis güncellendi")
            total_updated += count
            
            # 6. Notification
            print("\n6. Notification kayıtları güncelleniyor...")
            notifications = Notification.query.all()
            for n in notifications:
                if n.created_at:
                    n.created_at = n.created_at + timedelta(hours=3)
            count = len(notifications)
            print(f"   ✅ {count} notification güncellendi")
            total_updated += count
            
            # Commit
            db.session.commit()
            
            print("\n" + "="*60)
            print(f"✅ TOPLAM {total_updated} KAYIT GÜNCELLENDİ!")
            print("="*60)
            print("\nArtık tüm tarihler Türkiye saati (UTC+3) ile gösterilecek!")
            print("\n⚠️  Flask'ı yeniden başlatın:")
            print("   pkill -f 'python3 run.py' && python3 run.py")
            
        except Exception as e:
            print(f"\n❌ HATA: {e}")
            db.session.rollback()
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    migrate_utc_to_local()

