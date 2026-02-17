# -*- coding: utf-8 -*-
"""
Celery Tasks - Asenkron Video Analiz İşlemleri
"""
from app import create_app, db
from app.models import Session, Notification, AIAnalysis, ProgressAnalysis, Counselor
from app.services.audio_service import AudioService
from app.services.text_service import TextService
from app.services.emotion_service import EmotionService
from app.services.body_language_service import BodyLanguageService
from app.services.ai_service import AIService
from app.utils.file_handler import FileHandler
import json
import os
from datetime import datetime

# Flask app'i oluştur
flask_app = create_app()

# Celery'yi Flask app ile initialize et
from app.celery_config import make_celery
celery = make_celery(flask_app)


@celery.task(bind=True, name='app.tasks.analyze_video')
def analyze_video(self, session_id, counselor_id):
    """
    Video analiz görevi - Arka planda çalışır
    
    Args:
        session_id: Analiz edilecek oturum ID'si
        counselor_id: Danışman ID'si
    """
    print(f"\n{'='*60}")
    print(f"🚀 ARKA PLAN ANALİZ BAŞLADI")
    print(f"📋 Task ID: {self.request.id}")
    print(f"📝 Session ID: {session_id}")
    print(f"👤 Counselor ID: {counselor_id}")
    print(f"{'='*60}\n")
    
    # Flask app context içinde çalıştır
    with flask_app.app_context():
        try:
            # Session bilgisini al
            session = Session.query.get(session_id)
            if not session:
                raise Exception(f"Oturum bulunamadı: {session_id}")
            
            # Task ID'yi kaydet
            session.task_id = self.request.id
            session.analysis_status = 'processing'
            session.analysis_progress = 0
            db.session.commit()
            
            # Video yolunu al
            video_path = session.video_path
            if not video_path or not os.path.exists(video_path):
                raise Exception(f"Video dosyası bulunamadı: {video_path}")
            
            # Danışan bilgisi
            client_name = session.client.name
            
            # İlerleme: %5 - Başlangıç
            session.analysis_progress = 5
            db.session.commit()
            
            # 1. Ses analizi
            print("\n🎵 1/5 - SES ANALİZİ BAŞLIYOR...")
            file_handler = FileHandler()
            temp_audio = os.path.join(file_handler.temp_folder, f"temp_audio_{session_id}.wav")
            file_handler._convert_video_to_audio(video_path, temp_audio)
            
            audio_service = AudioService()
            audio_data = audio_service.analyze(video_path, temp_audio)
            print("✅ Ses analizi tamamlandı")
            session.analysis_progress = 25
            db.session.commit()
            
            # 2. Metin analizi
            print("\n📝 2/5 - METİN ANALİZİ BAŞLIYOR...")
            text_service = TextService()
            text_data = text_service.analyze(temp_audio)
            print("✅ Metin analizi tamamlandı")
            session.analysis_progress = 40
            db.session.commit()
            
            # Temp audio dosyasını sil
            if os.path.exists(temp_audio):
                os.remove(temp_audio)
            
            # 3. Duygu analizi
            print("\n😊 3/5 - DUYGU ANALİZİ BAŞLIYOR...")
            emotion_service = EmotionService()
            emotion_data = emotion_service.analyze(video_path)
            print("✅ Duygu analizi tamamlandı")
            session.analysis_progress = 60
            db.session.commit()
            
            # 4. Beden dili analizi
            print("\n🤸 4/5 - BEDEN DİLİ ANALİZİ BAŞLIYOR...")
            body_service = BodyLanguageService()
            body_data = body_service.analyze(video_path)
            print("✅ Beden dili analizi tamamlandı")
            session.analysis_progress = 80
            db.session.commit()
            
            # 5. AI Analizi
            print("\n🤖 5/5 - AI ANALİZ BAŞLIYOR...")
            ai_service = AIService()
            
            # Tüm verileri birleştir
            combined_data = {
                'session_id': session_id,
                'client_name': client_name,
                'audio_summary': audio_data,
                'text_analysis': text_data,
                'emotion_data': emotion_data,
                'body_data': body_data
            }
            
            ai_result = ai_service.analyze(combined_data)
            
            if ai_result['status'] == 'success':
                # Analiz sonuçlarını kaydet
                session.analysis_results = json.dumps(combined_data, ensure_ascii=False)
                session.analysis_status = 'completed'
                session.analysis_progress = 100
                
                # AI raporunu kaydet
                existing_ai_analysis = AIAnalysis.query.filter_by(
                    user_id=counselor_id,
                    session_id=session_id
                ).first()
                
                if existing_ai_analysis:
                    existing_ai_analysis.analysis_text = ai_result['analysis']
                    existing_ai_analysis.created_at = datetime.utcnow()
                else:
                    new_ai_analysis = AIAnalysis(
                        user_id=counselor_id,
                        session_id=session_id,
                        analysis_text=ai_result['analysis']
                    )
                    db.session.add(new_ai_analysis)
                
                db.session.commit()
                
                print("✅ AI analizi tamamlandı")
                print(f"\n{'='*60}")
                print("🎉 ANALİZ BAŞARIYLA TAMAMLANDI!")
                print(f"{'='*60}\n")
                
                # Başarı bildirimi oluştur
                notification = Notification(
                    counselor_id=counselor_id,
                    title="Analiz Tamamlandı! 🎉",
                    message=f"'{client_name}' adlı danışanınızın '{session.title}' oturum analizi başarıyla tamamlandı. Sonuçları görüntülemek için tıklayın.",
                    notification_type='success',
                    link=f"/session/view/{session_id}",
                    related_session_id=session_id
                )
                db.session.add(notification)
                db.session.commit()
                
                # E-posta bildirimi gönder
                try:
                    from app.services.email_service import send_analysis_completed_email
                    counselor = Counselor.query.get(counselor_id)
                    if counselor:
                        site_url = flask_app.config.get('SITE_URL', 'https://yakades.com.tr')
                        view_url = f"{site_url}/session/view/{session_id}"
                        send_analysis_completed_email(
                            counselor.email, counselor.name,
                            client_name, session.title, view_url
                        )
                except Exception as mail_err:
                    print(f"⚠️ E-posta gönderilemedi: {mail_err}")
                
                return {
                    'status': 'success',
                    'session_id': session_id,
                    'message': 'Analiz başarıyla tamamlandı'
                }
            else:
                raise Exception(ai_result.get('analysis', 'AI analizi başarısız'))
                
        except Exception as e:
            print(f"\n{'='*60}")
            print(f"❌ ANALİZ HATASI!")
            print(f"Hata: {str(e)}")
            print(f"{'='*60}\n")
            
            # Hata durumunu kaydet
            try:
                session = Session.query.get(session_id)
                if session:
                    session.analysis_status = 'failed'
                    session.analysis_progress = 0
                    db.session.commit()
                
                # Hata bildirimi oluştur
                notification = Notification(
                    counselor_id=counselor_id,
                    title="Analiz Başarısız! ❌",
                    message=f"'{session.client.name}' adlı danışanınızın '{session.title}' oturum analizi sırasında bir hata oluştu. Detaylar için tıklayın.",
                    notification_type='error',
                    link=f"/session/view/{session_id}",
                    related_session_id=session_id
                )
                db.session.add(notification)
                db.session.commit()
                
                # E-posta bildirimi gönder
                try:
                    from app.services.email_service import send_analysis_failed_email
                    counselor = Counselor.query.get(counselor_id)
                    if counselor and session:
                        site_url = flask_app.config.get('SITE_URL', 'https://yakades.com.tr')
                        view_url = f"{site_url}/session/view/{session_id}"
                        send_analysis_failed_email(
                            counselor.email, counselor.name,
                            session.client.name, session.title, view_url
                        )
                except Exception as mail_err:
                    print(f"⚠️ E-posta gönderilemedi: {mail_err}")
            except Exception as notify_error:
                print(f"⚠️ Bildirim oluşturulurken hata: {notify_error}")
                db.session.rollback()
            
            # Hatayı döndür (retry yapma, çünkü zaten failed durumu kaydedildi)
            return {
                'status': 'error',
                'session_id': session_id,
                'message': str(e)
            }


@celery.task(bind=True, name='app.tasks.analyze_progress', max_retries=0)
def analyze_progress(self, progress_analysis_id, counselor_id):
    """
    İlerleyiş analizi görevi - Arka planda çalışır
    
    Args:
        progress_analysis_id: Analiz edilecek ProgressAnalysis ID'si
        counselor_id: Danışman ID'si
    """
    print(f"\n{'='*60}")
    print(f"🚀 ARKA PLAN İLERLEYİŞ ANALİZİ BAŞLADI")
    print(f"📋 Task ID: {self.request.id}")
    print(f"📊 Progress Analysis ID: {progress_analysis_id}")
    print(f"👤 Counselor ID: {counselor_id}")
    print(f"⏰ Zaman: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    # Flask app context içinde çalıştır
    with flask_app.app_context():
        try:
            # ProgressAnalysis kaydını al
            progress_analysis = ProgressAnalysis.query.get(progress_analysis_id)
            if not progress_analysis:
                raise Exception(f"İlerleyiş analizi bulunamadı: {progress_analysis_id}")
            
            # Task ID'yi kaydet
            progress_analysis.task_id = self.request.id
            progress_analysis.analysis_status = 'processing'
            progress_analysis.analysis_progress = 0
            db.session.commit()
            
            print(f"📝 Danışan: {progress_analysis.client.name}")
            print(f"📅 Tarih Aralığı: {progress_analysis.date_range}")
            
            # İlerleme: %10 - Başlangıç
            progress_analysis.analysis_progress = 10
            db.session.commit()
            
            # Aralıktaki tüm oturumları getir
            sessions_in_range = Session.query.filter(
                Session.client_id == progress_analysis.client_id,
                Session.date >= progress_analysis.start_session.date,
                Session.date <= progress_analysis.end_session.date
            ).order_by(Session.date.asc()).all()
            
            print(f"📊 {len(sessions_in_range)} oturum bulundu")
            
            # İlerleme: %20 - Oturumlar toplandı
            progress_analysis.analysis_progress = 20
            db.session.commit()
            
            # Oturum analizlerini hazırla
            session_analyses = []
            for i, session in enumerate(sessions_in_range):
                analysis_data = {
                    'id': session.id,
                    'title': session.title,
                    'date': session.date,
                    'notes': session.notes or ""
                }
                
                # AI analizini varsa ekle
                ai_analysis = AIAnalysis.query.filter_by(
                    session_id=session.id, 
                    user_id=counselor_id
                ).first()
                if ai_analysis:
                    analysis_data['ai_analysis'] = ai_analysis.analysis_text
                
                # Oturum analiz sonuçlarını varsa ekle
                if session.analysis_results:
                    analysis_data['analysis_results'] = session.analysis_results
                
                session_analyses.append(analysis_data)
                
                # Her oturum için ilerleme güncelle (20-60 arası)
                progress = 20 + int((i + 1) / len(sessions_in_range) * 40)
                progress_analysis.analysis_progress = progress
                db.session.commit()
            
            print(f"✅ {len(session_analyses)} oturum verisi hazırlandı")
            
            # İlerleme: %60 - Veriler hazırlandı
            progress_analysis.analysis_progress = 60
            db.session.commit()
            
            if len(session_analyses) < 2:
                raise Exception('Seçilen aralıkta yeterli oturum bulunamadı.')
            
            # AI ile ilerleyiş analizi yap
            print("\n🤖 AI İLE İLERLEYİŞ ANALİZİ BAŞLIYOR...")
            ai_service = AIService()
            progress_result = ai_service.analyze_progress(
                client_name=progress_analysis.client.name,
                session_analyses=session_analyses,
                date_range=progress_analysis.date_range
            )
            
            # İlerleme: %80 - AI analizi tamamlandı
            progress_analysis.analysis_progress = 80
            db.session.commit()
            
            if progress_result.get('status') == 'error':
                raise Exception(progress_result.get('analysis', 'AI analizi başarısız'))
            
            # Analiz sonucunu kaydet
            progress_analysis.analysis_text = progress_result['analysis']
            progress_analysis.analysis_status = 'completed'
            progress_analysis.analysis_progress = 100
            db.session.commit()
            
            print("✅ İlerleyiş analizi tamamlandı")
            print(f"\n{'='*60}")
            print("🎉 İLERLEYİŞ ANALİZİ BAŞARIYLA TAMAMLANDI!")
            print(f"{'='*60}\n")
            
            # Başarı bildirimi oluştur
            notification = Notification(
                counselor_id=counselor_id,
                title="İlerleyiş Analizi Tamamlandı! 📊",
                message=f"'{progress_analysis.client.name}' adlı danışanınızın ({progress_analysis.date_range}) ilerleyiş analizi başarıyla tamamlandı. Raporu görüntülemek için tıklayın.",
                notification_type='success',
                link=f"/view_progress_report/{progress_analysis_id}"
            )
            db.session.add(notification)
            db.session.commit()
            
            # E-posta bildirimi gönder
            try:
                from app.services.email_service import send_progress_completed_email
                counselor = Counselor.query.get(counselor_id)
                if counselor:
                    site_url = flask_app.config.get('SITE_URL', 'https://yakades.com.tr')
                    view_url = f"{site_url}/view_progress_report/{progress_analysis_id}"
                    send_progress_completed_email(
                        counselor.email, counselor.name,
                        progress_analysis.client.name,
                        progress_analysis.date_range, view_url
                    )
            except Exception as mail_err:
                print(f"⚠️ E-posta gönderilemedi: {mail_err}")
            
            return {
                'status': 'success',
                'progress_analysis_id': progress_analysis_id,
                'message': 'İlerleyiş analizi başarıyla tamamlandı'
            }
                
        except Exception as e:
            print(f"\n{'='*60}")
            print(f"❌ İLERLEYİŞ ANALİZİ HATASI!")
            print(f"Hata: {str(e)}")
            print(f"{'='*60}\n")
            
            # Hata durumunu kaydet
            try:
                progress_analysis = ProgressAnalysis.query.get(progress_analysis_id)
                if progress_analysis:
                    progress_analysis.analysis_status = 'failed'
                    progress_analysis.analysis_progress = 0
                    progress_analysis.analysis_text = f"Analiz hatası: {str(e)}"
                    db.session.commit()
                
                # Hata bildirimi oluştur
                notification = Notification(
                    counselor_id=counselor_id,
                    title="İlerleyiş Analizi Başarısız! ❌",
                    message=f"İlerleyiş analizi sırasında bir hata oluştu: {str(e)}",
                    notification_type='error',
                    link=f"/progress_analysis/{progress_analysis.client_id}"
                )
                db.session.add(notification)
                db.session.commit()
                
                # E-posta bildirimi gönder
                try:
                    from app.services.email_service import send_progress_failed_email
                    counselor = Counselor.query.get(counselor_id)
                    if counselor and progress_analysis:
                        send_progress_failed_email(
                            counselor.email, counselor.name,
                            progress_analysis.client.name, str(e)
                        )
                except Exception as mail_err:
                    print(f"⚠️ E-posta gönderilemedi: {mail_err}")
            except Exception as notify_error:
                print(f"⚠️ Bildirim oluşturulurken hata: {notify_error}")
                db.session.rollback()
            
            return {
                'status': 'error',
                'progress_analysis_id': progress_analysis_id,
                'message': str(e)
            }


@celery.task(name='app.tasks.cleanup_old_notifications')
def cleanup_old_notifications():
    """30 günden eski bildirimleri temizle"""
    with flask_app.app_context():
        try:
            from datetime import timedelta
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            
            old_notifications = Notification.query.filter(
                Notification.created_at < thirty_days_ago,
                Notification.is_read == True
            ).all()
            
            count = len(old_notifications)
            for notification in old_notifications:
                db.session.delete(notification)
            
            db.session.commit()
            print(f"🧹 {count} eski bildirim temizlendi")
            
            return {'status': 'success', 'deleted_count': count}
        except Exception as e:
            print(f"❌ Bildirim temizleme hatası: {e}")
            db.session.rollback()
            return {'status': 'error', 'error': str(e)}
