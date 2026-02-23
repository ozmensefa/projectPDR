# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, request, jsonify, send_file, abort, flash, redirect, url_for
from flask_login import login_required, current_user
from app.services.audio_service import AudioService
from app.services.text_service import TextService
from app.services.emotion_service import EmotionService
from app.services.body_language_service import BodyLanguageService
from app.services.ai_service import AIService
from app.utils.file_handler import FileHandler
from app.models import Client, Session, AIAnalysis, ProgressAnalysis, Notification, Counselor, UserActivity
from app.models import get_turkey_time
from werkzeug.utils import secure_filename
import os
import time
from datetime import datetime
from app import db

main_bp = Blueprint('main', __name__)



def generate_suggestions(clients, upcoming_sessions, recent_sessions):
    """Danışan durumlarına göre öneriler oluştur"""
    suggestions = []
    from datetime import datetime, timedelta
    now = datetime.now()
    
    # Danışan sayısına göre öneriler
    if len(clients) == 0:
        suggestions.append({
            'type': 'info',
            'icon': 'fas fa-user-plus',
            'title': 'İlk Danışanınızı Ekleyin',
            'description': 'Sistemi kullanmaya başlamak için ilk danışanınızı ekleyebilirsiniz.',
            'action': 'Danışan Ekle',
            'url': 'client.add_client'
        })
    elif len(clients) < 3:
        suggestions.append({
            'type': 'tip',
            'icon': 'fas fa-lightbulb',
            'title': 'Daha Fazla Danışan',
            'description': f'Şu anda {len(clients)} danışanınız var. Sistemi daha verimli kullanmak için daha fazla danışan ekleyebilirsiniz.',
            'action': 'Danışan Ekle',
            'url': 'client.add_client'
        })
    
    # Analiz edilmemiş oturumlar için öneriler
    unanalyzed_sessions = []
    for client in clients:
        for session in client.sessions:
            if session.date <= now and not session.analysis_results:
                unanalyzed_sessions.append(session)
    
    if unanalyzed_sessions:
        suggestions.append({
            'type': 'warning',
            'icon': 'fas fa-chart-line',
            'title': 'Bekleyen Analizler',
            'description': f'{len(unanalyzed_sessions)} oturumunuz analiz bekliyor. Raporları oluşturmak için analizleri tamamlayın.',
            'action': 'Analizleri Görüntüle',
            'url': 'client.list_clients'
        })
    
    # Yaklaşan oturumlar için öneriler
    if upcoming_sessions:
        tomorrow_sessions = [s for s in upcoming_sessions if s.date.date() == (now + timedelta(days=1)).date()]
        if tomorrow_sessions:
            suggestions.append({
                'type': 'info',
                'icon': 'fas fa-calendar-day',
                'title': 'Yarınki Oturumlar',
                'description': f'Yarın {len(tomorrow_sessions)} oturumunuz var. Hazırlıklarınızı tamamlamayı unutmayın.',
                'action': 'Oturumları Görüntüle',
                'url': 'client.list_clients'
            })
    else:
        suggestions.append({
            'type': 'tip',
            'icon': 'fas fa-calendar-plus',
            'title': 'Oturum Planlama',
            'description': 'Yaklaşan oturumunuz bulunmuyor. Danışanlarınız için yeni oturumlar planlayabilirsiniz.',
            'action': 'Oturum Planla',
            'url': 'client.list_clients'
        })
    
    # Uzun süredir oturumu olmayan danışanlar
    inactive_clients = []
    one_month_ago = now - timedelta(days=30)
    for client in clients:
        if not client.sessions:
            inactive_clients.append(client)
        else:
            last_session = max(client.sessions, key=lambda s: s.date)
            if last_session.date < one_month_ago:
                inactive_clients.append(client)
    
    if inactive_clients:
        suggestions.append({
            'type': 'warning',
            'icon': 'fas fa-user-clock',
            'title': 'Pasif Danışanlar',
            'description': f'{len(inactive_clients)} danışanınızın son 1 aydır oturumu yok. İletişime geçmeyi düşünebilirsiniz.',
            'action': 'Danışanları Görüntüle',
            'url': 'client.list_clients'
        })
    
    # AI analizi olmayan oturumlar
    sessions_without_ai = []
    for client in clients:
        for session in client.sessions:
            if session.analysis_results and not session.ai_analyses:
                sessions_without_ai.append(session)
    
    if sessions_without_ai:
        suggestions.append({
            'type': 'tip',
            'icon': 'fas fa-robot',
            'title': 'AI Analizi Önerisi',
            'description': f'{len(sessions_without_ai)} oturumunuz için AI analizi yapılabilir. Daha detaylı raporlar elde edebilirsiniz.',
            'action': 'AI Analizlerini Görüntüle',
            'url': 'client.list_clients'
        })
    
    # Başarı mesajları
    if len(clients) >= 5 and len([s for s in recent_sessions if s.analysis_results]) >= 2:
        suggestions.append({
            'type': 'success',
            'icon': 'fas fa-trophy',
            'title': 'Harika İlerleme!',
            'description': f'{len(clients)} danışanınız var ve son oturumlarınızı düzenli olarak analiz ediyorsunuz. Mükemmel!',
            'action': 'İstatistikleri Görüntüle',
            'url': 'client.list_clients'
        })
    
    # En fazla 4 öneri göster
    return suggestions[:4]

@main_bp.route('/')
def index():
    clients = []
    upcoming_sessions = []
    recent_sessions = []
    suggestions = []
    
    if current_user.is_authenticated:
        clients = Client.query.filter_by(counselor_id=current_user.id).all()
        
        # Yaklaşan oturumları getir (gelecek tarihli oturumlar)
        from datetime import datetime
        now = datetime.now()
        upcoming_sessions = Session.query.join(Client).filter(
            Client.counselor_id == current_user.id,
            Session.date > now
        ).order_by(Session.date.asc()).limit(10).all()
        
        # Geçmiş oturumları getir (geçen tarihli oturumlar, en son 3 tanesi)
        recent_sessions = Session.query.join(Client).filter(
            Client.counselor_id == current_user.id,
            Session.date <= now
        ).order_by(Session.date.desc()).limit(3).all()
        
        # Her danışan için son tamamlanmış oturum ve gelecek oturum bilgilerini hesapla
        for client in clients:
            # Son tamamlanmış oturum (geçmiş + analiz sonucu var)
            client.last_completed_session = Session.query.filter(
                Session.client_id == client.id,
                Session.date <= now,
                Session.analysis_results.isnot(None)
            ).order_by(Session.date.desc()).first()
            
            # Gelecek oturum (gelecek tarihli)
            client.next_session = Session.query.filter(
                Session.client_id == client.id,
                Session.date > now
            ).order_by(Session.date.asc()).first()
        
        # Önerileri oluştur
        suggestions = generate_suggestions(clients, upcoming_sessions, recent_sessions)
    
    return render_template('index.html', 
                         clients=clients, 
                         upcoming_sessions=upcoming_sessions, 
                         recent_sessions=recent_sessions,
                         suggestions=suggestions)

@main_bp.route('/calendar')
@login_required
def calendar():
    """Takvim sayfası"""
    from datetime import datetime, timedelta
    import calendar as cal
    
    # Tarih parametrelerini al
    year = request.args.get('year', datetime.now().year, type=int)
    month = request.args.get('month', datetime.now().month, type=int)
    
    # Geçerli tarih aralığında tut
    if month < 1:
        month = 12
        year -= 1
    elif month > 12:
        month = 1
        year += 1
    
    # Ayın ilk ve son günlerini hesapla
    first_day = datetime(year, month, 1)
    if month == 12:
        last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = datetime(year, month + 1, 1) - timedelta(days=1)
    
    # Bu ay içindeki tüm oturumları getir
    sessions = Session.query.join(Client).filter(
        Client.counselor_id == current_user.id,
        Session.date >= first_day,
        Session.date <= last_day.replace(hour=23, minute=59, second=59)
    ).order_by(Session.date.asc()).all()
    
    # Oturumları tarihlere göre grupla
    sessions_by_date = {}
    for session in sessions:
        date_key = session.date.date()
        if date_key not in sessions_by_date:
            sessions_by_date[date_key] = []
        sessions_by_date[date_key].append(session)
    
    # Bugünün tarihini al
    today = datetime.now()
    
    # Türkçe ay isimleri
    turkish_months = {
        1: 'Ocak', 2: 'Şubat', 3: 'Mart', 4: 'Nisan',
        5: 'Mayıs', 6: 'Haziran', 7: 'Temmuz', 8: 'Ağustos',
        9: 'Eylül', 10: 'Ekim', 11: 'Kasım', 12: 'Aralık'
    }
    
    # Takvim bilgilerini hazırla
    calendar_data = {
        'year': year,
        'month': month,
        'month_name': turkish_months[month],
        'prev_month': month - 1 if month > 1 else 12,
        'prev_year': year if month > 1 else year - 1,
        'next_month': month + 1 if month < 12 else 1,
        'next_year': year if month < 12 else year + 1,
        'weeks': cal.monthcalendar(year, month),
        'sessions_by_date': sessions_by_date,
        'today': today
    }
    
    return render_template('calendar.html', calendar=calendar_data)

@main_bp.route('/api/calendar-events')
@login_required
def calendar_events():
    """FullCalendar için JSON event verileri"""
    from datetime import datetime
    
    start = request.args.get('start', '')
    end = request.args.get('end', '')
    
    try:
        start_date = datetime.fromisoformat(start.replace('Z', '+00:00').split('T')[0])
        end_date = datetime.fromisoformat(end.replace('Z', '+00:00').split('T')[0])
    except (ValueError, IndexError):
        start_date = datetime.now().replace(day=1)
        end_date = datetime.now()
    
    sessions = Session.query.join(Client).filter(
        Client.counselor_id == current_user.id,
        Session.date >= start_date,
        Session.date <= end_date
    ).order_by(Session.date.asc()).all()
    
    now = datetime.now()
    events = []
    for s in sessions:
        is_past = s.date < now
        is_completed = s.analysis_results is not None
        
        if is_past and is_completed:
            color = '#4caf50'
            status = 'Tamamlandı'
        elif is_past and not is_completed:
            color = '#f44336'
            status = 'Tamamlanmamış'
        else:
            color = '#2196f3'
            status = 'Yaklaşan'
        
        events.append({
            'id': s.id,
            'title': s.title,
            'start': s.date.isoformat(),
            'url': url_for('client.view_session', session_id=s.id),
            'color': color,
            'extendedProps': {
                'clientName': s.client.name,
                'status': status,
                'time': s.date.strftime('%H:%M')
            }
        })
    
    return jsonify(events)

@main_bp.route('/save_analysis/<int:session_id>', methods=['POST'])
@login_required
def save_analysis(session_id):
    try:
        data = request.get_json()
        print("\n=== GELEN VERİ ===")
        print(type(data))
        print(data)
        print("=================\n")

        session = Session.query.get_or_404(session_id)
        if session.client.counselor_id != current_user.id:
            abort(403)

        if not data or 'ai' not in data:
            return jsonify({'success': False, 'message': 'Geçersiz veri formatı'}), 400

        ai_data = data['ai']
        if not isinstance(ai_data, dict) or 'analysis' not in ai_data:
            return jsonify({'success': False, 'message': 'Geçersiz AI veri formatı'}), 400

        analysis_text = ai_data['analysis']
        if not analysis_text:
            return jsonify({'success': False, 'message': 'Analiz metni boş'}), 400

        print("\n=== KAYDEDİLECEK VERİ ===")
        print(type(analysis_text))
        print(analysis_text)
        print("=========================\n")

        # Direkt olarak metni kaydet
        session.analysis_results = str(analysis_text)
        db.session.commit()

        # Kaydedilen veriyi kontrol et
        saved_session = Session.query.get(session_id)
        print("\n=== KAYIT SONRASI KONTROL ===")
        print(f"Session ID: {saved_session.id}")
        print(f"Kaydedilen veri: {saved_session.analysis_results}")
        print("===========================\n")

        return jsonify({
            'success': True,
            'message': 'Analiz başarıyla kaydedildi'
        })

    except Exception as e:
        print("\n=== HATA OLUŞTU ===")
        print(str(e))
        print("==================\n")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Hata: {str(e)}'
        }), 500

@main_bp.route('/analyze_audio', methods=['POST'])
def analyze_audio():
    try:
        if 'video' not in request.files:
            return jsonify({'error': 'Video dosyası bulunamadı'}), 400

        video_file = request.files['video']
        if video_file.filename == '':
            return jsonify({'error': 'Dosya seçilmedi'}), 400

        file_handler = FileHandler()
        temp_video, temp_audio = file_handler.save_temp_files(video_file)

        audio_service = AudioService()
        result = audio_service.analyze(temp_video, temp_audio)

        file_handler.cleanup_temp_files([temp_video, temp_audio])
        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main_bp.route('/analyze_text', methods=['POST'])
def analyze_text():
    try:
        if 'video' not in request.files:
            return jsonify({'error': 'Video dosyası bulunamadı'}), 400

        video_file = request.files['video']
        if video_file.filename == '':
            return jsonify({'error': 'Dosya seçilmedi'}), 400

        file_handler = FileHandler()
        temp_video, temp_audio = file_handler.save_temp_files(video_file)

        text_service = TextService()
        result = text_service.analyze(temp_audio)

        file_handler.cleanup_temp_files([temp_video, temp_audio])

        # Sonucu dosya olarak gönder
        return jsonify(result)

    except Exception as e:
        import traceback
        print(f"❌ Metin analizi hatası: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@main_bp.route('/analyze_emotion', methods=['POST'])
def analyze_emotion():
    try:
        if 'video' not in request.files:
            return jsonify({'error': 'Video dosyası bulunamadı'}), 400

        video_file = request.files['video']
        if video_file.filename == '':
            return jsonify({'error': 'Dosya seçilmedi'}), 400

        file_handler = FileHandler()
        temp_video = file_handler.save_video_file(video_file)

        emotion_service = EmotionService()
        result = emotion_service.analyze(temp_video)

        file_handler.cleanup_temp_files([temp_video])
        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main_bp.route('/analyze_body_language', methods=['POST'])
def analyze_body_language():
    try:
        if 'video' not in request.files:
            return jsonify({'error': 'Video dosyası bulunamadı'}), 400

        video_file = request.files['video']
        if video_file.filename == '':
            return jsonify({'error': 'Dosya seçilmedi'}), 400

        file_handler = FileHandler()
        temp_video = file_handler.save_video_file(video_file)

        body_language_service = BodyLanguageService()
        result = body_language_service.analyze(temp_video)

        file_handler.cleanup_temp_files([temp_video])
        return jsonify(result)

    except Exception as e:
        import traceback
        print(f"❌ Beden dili analizi hatası: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@main_bp.route('/analyze_ai', methods=['POST'])
@login_required
def analyze_ai():
    try:
        analysis_data = request.get_json()
        if not analysis_data:
            return jsonify({'error': 'Analiz verisi bulunamadı'}), 400

        # Danışan adını ve oturum ID'sini al
        session_id = analysis_data.get('session_id')
        client_name = analysis_data.get('client_name', 'Bilinmiyor')
        
        # Eğer session_id varsa, veritabanından danışan adını al
        if session_id:
            from app.database_utils import safe_db_query
            
            def get_client_name():
                session = Session.query.get(session_id)
                if session and session.client:
                    return session.client.name
                return None
            
            db_client_name = safe_db_query(get_client_name, None)
            if db_client_name:
                client_name = db_client_name
        
        # Danışan adını analiz verilerine ekle
        analysis_data['client_name'] = client_name
        
        print("Gelen analiz verisi:", analysis_data)
        
        try:
            ai_service = AIService()
            result = ai_service.analyze(analysis_data)
            
            # Sonucu kontrol et
            if result.get('status') == 'error':
                return jsonify({'error': result.get('analysis', 'Bilinmeyen hata')}), 500
            
            return jsonify(result)
            
        except ValueError as ve:
            # API key hatası
            print(f"API key hatası: {str(ve)}")
            return jsonify({'error': 'API yapılandırma hatası. Lütfen sistem yöneticisiyle iletişime geçin.'}), 500
        except Exception as e:
            # Diğer hatalar
            print(f"AI servis hatası: {str(e)}")
            return jsonify({'error': f'AI analiz servisi hatası: {str(e)}'}), 500

    except Exception as e:
        print(f"Genel hata: {str(e)}")
        return jsonify({'error': f'Beklenmeyen hata: {str(e)}'}), 500

@main_bp.route('/save_ai_analysis/<int:session_id>', methods=['POST'])
@login_required
def save_ai_analysis(session_id):
    try:
        analysis_text = request.form.get('analysis_text')
        
        if not analysis_text:
            flash('Analiz metni boş olamaz.', 'error')
            return redirect(url_for('client.view_session', session_id=session_id))
        
        # Eğer analiz zaten kaydedilmişse, tekrar kaydetme
        existing_analysis = AIAnalysis.query.filter_by(
            user_id=current_user.id, 
            session_id=session_id
        ).first()
        
        if existing_analysis:
            existing_analysis.analysis_text = analysis_text
            existing_analysis.created_at = datetime.utcnow()
            db.session.commit()
            flash('Analiz başarıyla güncellendi.', 'success')
        else:
            new_analysis = AIAnalysis(
                user_id=current_user.id,
                session_id=session_id,
                analysis_text=analysis_text
            )
            db.session.add(new_analysis)
            db.session.commit()
            flash('Analiz başarıyla kaydedildi.', 'success')
        
        return redirect(url_for('client.view_session', session_id=session_id))
    
    except Exception as e:
        import traceback
        print(f"Hata: {str(e)}")
        print(traceback.format_exc())
        flash(f'Analiz kaydedilirken bir hata oluştu: {str(e)}', 'error')
        return redirect(url_for('client.view_session', session_id=session_id))

@main_bp.route('/delete_ai_analysis/<int:session_id>', methods=['POST'])
@login_required
def delete_ai_analysis(session_id):
    try:
        # AI analizini bul
        ai_analysis = AIAnalysis.query.filter_by(
            user_id=current_user.id, 
            session_id=session_id
        ).first()
        
        if not ai_analysis:
            flash('Silinecek AI analizi bulunamadı.', 'warning')
            return redirect(url_for('client.view_session', session_id=session_id))
        
        # AI analizini sil
        db.session.delete(ai_analysis)
        db.session.commit()
        
        flash('AI analizi başarıyla silindi.', 'success')
        return redirect(url_for('client.view_session', session_id=session_id))
    
    except Exception as e:
        import traceback
        print(f"AI analizi silme hatası: {str(e)}")
        print(traceback.format_exc())
        flash(f'AI analizi silinirken bir hata oluştu: {str(e)}', 'error')
        return redirect(url_for('client.view_session', session_id=session_id)) 

# İlerleyiş Analizi Route'ları
@main_bp.route('/progress_analysis/<int:client_id>')
@login_required
def progress_analysis(client_id):
    """İlerleyiş analizi aralık seçimi sayfası"""
    client = Client.query.get_or_404(client_id)
    
    # Danışanın bu kullanıcıya ait olup olmadığını kontrol et
    if client.counselor_id != current_user.id:
        abort(403)
    
    # Danışanın tüm oturumlarını tarih sırasında getir
    sessions = Session.query.filter_by(client_id=client_id).order_by(Session.date.asc()).all()
    
    if len(sessions) < 2:
        flash('İlerleyiş analizi için en az 2 oturum gereklidir.', 'warning')
        return redirect(url_for('client.view_client', client_id=client_id))
    
    # Önceki ilerleyiş analizlerini getir
    previous_analyses = ProgressAnalysis.query.filter_by(
        client_id=client_id,
        counselor_id=current_user.id
    ).order_by(ProgressAnalysis.created_at.desc()).all()
    
    return render_template('progress_analysis.html', 
                         client=client, 
                         sessions=sessions,
                         previous_analyses=previous_analyses)

@main_bp.route('/generate_progress_report/<int:client_id>', methods=['POST'])
@login_required
def generate_progress_report(client_id):
    """İlerleyiş raporu oluştur - Celery ile arka planda işle"""
    try:
        print(f"\n{'='*60}")
        print(f"📋 GENERATE PROGRESS REPORT ÇAĞRILDI")
        print(f"📋 Client ID: {client_id}")
        print(f"📋 Current User ID: {current_user.id}")
        print(f"📋 Request Method: {request.method}")
        print(f"📋 Request Form: {dict(request.form)}")
        print(f"{'='*60}\n")
        
        client = Client.query.get_or_404(client_id)
        
        # Danışanın bu kullanıcıya ait olup olmadığını kontrol et
        if client.counselor_id != current_user.id:
            print(f"❌ Yetki hatası: client.counselor_id={client.counselor_id} != current_user.id={current_user.id}")
            flash('Bu danışana erişim yetkiniz yok.', 'error')
            return redirect(url_for('client.list_clients'))
        
        # Form verilerini al
        start_session_id_raw = request.form.get('start_session_id')
        end_session_id_raw = request.form.get('end_session_id')
        
        print(f"📊 Start Session ID (raw): '{start_session_id_raw}' (type: {type(start_session_id_raw)})")
        print(f"📊 End Session ID (raw): '{end_session_id_raw}' (type: {type(end_session_id_raw)})")
        
        # Boş string kontrolü
        if not start_session_id_raw or not end_session_id_raw or start_session_id_raw == '' or end_session_id_raw == '':
            flash('Başlangıç ve bitiş oturumları seçilmelidir.', 'error')
            return redirect(url_for('main.progress_analysis', client_id=client_id))
        
        # Integer'a çevir
        try:
            start_session_id = int(start_session_id_raw)
            end_session_id = int(end_session_id_raw)
        except (ValueError, TypeError):
            print(f"❌ Integer dönüşüm hatası!")
            flash('Geçersiz oturum seçimi.', 'error')
            return redirect(url_for('main.progress_analysis', client_id=client_id))
        
        print(f"📊 Start Session ID: {start_session_id}")
        print(f"📊 End Session ID: {end_session_id}")
        
        # Oturumları getir ve tarih kontrolü yap
        start_session = Session.query.get_or_404(start_session_id)
        end_session = Session.query.get_or_404(end_session_id)
        
        if start_session.date > end_session.date:
            flash('Başlangıç oturumu bitiş oturumundan sonra olamaz.', 'error')
            return redirect(url_for('main.progress_analysis', client_id=client_id))
        
        if start_session_id == end_session_id:
            flash('Başlangıç ve bitiş oturumları aynı olamaz.', 'error')
            return redirect(url_for('main.progress_analysis', client_id=client_id))
        
        # Aralıktaki tüm oturumları getir
        sessions_in_range = Session.query.filter(
            Session.client_id == client_id,
            Session.date >= start_session.date,
            Session.date <= end_session.date
        ).order_by(Session.date.asc()).all()
        
        if len(sessions_in_range) < 2:
            flash('Seçilen aralıkta yeterli oturum bulunamadı.', 'error')
            return redirect(url_for('main.progress_analysis', client_id=client_id))
        
        # Tarih aralığını formatla
        date_range = f"{start_session.date.strftime('%d.%m.%Y')} - {end_session.date.strftime('%d.%m.%Y')}"
        
        # ProgressAnalysis kaydını oluştur (analiz sonucu olmadan)
        progress_analysis = ProgressAnalysis(
            counselor_id=current_user.id,
            client_id=client_id,
            start_session_id=start_session_id,
            end_session_id=end_session_id,
            sessions_analyzed=len(sessions_in_range),
            date_range=date_range,
            analysis_status='pending',
            analysis_progress=0
        )
        
        db.session.add(progress_analysis)
        db.session.commit()
        
        # Celery task'ını başlat
        from app.tasks import analyze_progress
        task = analyze_progress.apply_async(
            args=[progress_analysis.id, current_user.id],
            countdown=1  # 1 saniye gecikme ile başlat (DB commit'in tamamlanması için)
        )
        
        # Task ID'yi kaydet
        progress_analysis.task_id = task.id
        progress_analysis.analysis_status = 'processing'
        db.session.commit()
        
        print(f"🚀 İlerleyiş analizi arka planda başlatıldı - Task ID: {task.id}")
        
        flash(
            f'✅ İlerleyiş analizi başarıyla başlatıldı! '
            f'{len(sessions_in_range)} oturum arka planda analiz edilecek. '
            f'Tamamlandığında bildirim alacaksınız.',
            'success'
        )
        return redirect(url_for('main.view_progress_report', report_id=progress_analysis.id))
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"❌ İlerleyiş raporu oluşturma hatası:")
        print(f"   Hata: {str(e)}")
        print(f"   Traceback:\n{error_trace}")
        db.session.rollback()
        flash(f'İlerleyiş raporu oluşturulurken hata oluştu: {str(e)}', 'error')
        return redirect(url_for('main.progress_analysis', client_id=client_id))

@main_bp.route('/view_progress_report/<int:report_id>')
@login_required
def view_progress_report(report_id):
    """İlerleyiş raporu görüntüleme"""
    report = ProgressAnalysis.query.get_or_404(report_id)
    
    # Raporun bu kullanıcıya ait olup olmadığını kontrol et
    if report.counselor_id != current_user.id:
        abort(403)
    
    return render_template('view_progress_report.html', report=report)

@main_bp.route('/delete_progress_report/<int:report_id>', methods=['POST'])
@login_required
def delete_progress_report(report_id):
    """İlerleyiş raporu silme"""
    try:
        report = ProgressAnalysis.query.get_or_404(report_id)
        
        # Raporun bu kullanıcıya ait olup olmadığını kontrol et
        if report.counselor_id != current_user.id:
            abort(403)
        
        client_id = report.client_id
        
        db.session.delete(report)
        db.session.commit()
        
        flash('İlerleyiş raporu başarıyla silindi.', 'success')
        return redirect(url_for('main.progress_analysis', client_id=client_id))
        
    except Exception as e:
        print(f"İlerleyiş raporu silme hatası: {str(e)}")
        db.session.rollback()
        flash(f'İlerleyiş raporu silinirken hata oluştu: {str(e)}', 'error')
        return redirect(url_for('main.progress_analysis', client_id=client_id))

@main_bp.route('/delete_complete_analysis/<int:session_id>', methods=['POST'])
@login_required
def delete_complete_analysis(session_id):
    """Oturum için hem AI analizini hem de oturum analizini siler"""
    try:
        # Oturumu al ve yetki kontrolü yap
        session = Session.query.get_or_404(session_id)
        if session.client.counselor_id != current_user.id:
            abort(403)
        
        # AI analizini sil
        ai_analysis = AIAnalysis.query.filter_by(
            user_id=current_user.id, 
            session_id=session_id
        ).first()
        
        if ai_analysis:
            db.session.delete(ai_analysis)
        
        # Oturum analiz sonuçlarını temizle
        session.analysis_results = None
        
        # Değişiklikleri kaydet
        db.session.commit()
        
        flash('Oturum analizi başarıyla silindi.', 'success')
        return redirect(url_for('client.view_session', session_id=session_id))
    
    except Exception as e:
        print(f"Tam analiz silme hatası: {str(e)}")
        db.session.rollback()
        flash(f'Analiz silinirken bir hata oluştu: {str(e)}', 'error')
        return redirect(url_for('client.view_session', session_id=session_id))


# ============================================================================
# RAPOR İNDİRME ENDPOINT'LERİ (PDF, DOCX, TXT)
# ============================================================================

def strip_html_tags(html_text):
    """HTML etiketlerini temizleyip düz metin döndürür"""
    import re
    if not html_text:
        return ''
    # <br> ve <br/> → newline
    text = re.sub(r'<br\s*/?>', '\n', html_text)
    # <p>, </p>, <div>, </div> → newline
    text = re.sub(r'</(p|div|li|tr|h[1-6])>', '\n', text)
    text = re.sub(r'<(p|div|li|tr|h[1-6])[^>]*>', '', text)
    # Diğer tüm HTML etiketlerini sil
    text = re.sub(r'<[^>]+>', '', text)
    # HTML entities
    text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&nbsp;', ' ').replace('&#39;', "'").replace('&quot;', '"')
    # Fazladan boş satırları temizle
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

@main_bp.route('/download_session_report/<int:session_id>/<format_type>')
@login_required
def download_session_report(session_id, format_type):
    """Oturum analiz raporunu belirtilen formatta indir"""
    try:
        session_obj = Session.query.get_or_404(session_id)
        if session_obj.client.counselor_id != current_user.id:
            abort(403)
        
        # AI analizini al
        saved_analysis = AIAnalysis.query.filter_by(session_id=session_id).first()
        if not saved_analysis:
            flash('İndirilecek analiz raporu bulunamadı.', 'warning')
            return redirect(url_for('client.view_session', session_id=session_id))
        
        analysis_text = strip_html_tags(saved_analysis.analysis_text)
        client_name = session_obj.client.name
        session_date = session_obj.date.strftime('%d-%m-%Y')
        counselor_name = current_user.name
        notes = session_obj.notes or ''
        
        file_name = f"{client_name}_oturum_analizi_{session_date}"
        
        if format_type == 'txt':
            return _generate_txt(analysis_text, notes, file_name,
                                 report_type='Oturum Analiz Raporu',
                                 client_name=client_name, counselor_name=counselor_name,
                                 extra_info=f"Tarih: {session_date}")
        elif format_type == 'pdf':
            return _generate_pdf(analysis_text, notes, file_name,
                                 report_type='Oturum Analiz Raporu',
                                 client_name=client_name, counselor_name=counselor_name,
                                 extra_info=f"Tarih: {session_date}")
        elif format_type == 'docx':
            return _generate_docx(analysis_text, notes, file_name,
                                  report_type='Oturum Analiz Raporu',
                                  client_name=client_name, counselor_name=counselor_name,
                                  extra_info=f"Tarih: {session_date}")
        else:
            abort(400)
    except Exception as e:
        import traceback
        print(f"Rapor indirme hatası: {traceback.format_exc()}")
        flash(f'Rapor indirilirken hata oluştu: {str(e)}', 'error')
        return redirect(url_for('client.view_session', session_id=session_id))

@main_bp.route('/download_progress_report/<int:report_id>/<format_type>')
@login_required
def download_progress_report_file(report_id, format_type):
    """İlerleyiş raporunu belirtilen formatta indir"""
    try:
        report = ProgressAnalysis.query.get_or_404(report_id)
        if report.counselor_id != current_user.id:
            abort(403)
        
        if not report.analysis_text:
            flash('İndirilecek analiz raporu bulunamadı.', 'warning')
            return redirect(url_for('main.view_progress_report', report_id=report_id))
        
        analysis_text = strip_html_tags(report.analysis_text)
        client_name = report.client.name
        counselor_name = report.counselor.name
        date_range = report.date_range
        file_name = f"{client_name}_ilerleme_raporu_{date_range.replace(' ', '_')}"
        
        extra_info = (f"Tarih Aralığı: {date_range}\n"
                      f"Analiz Edilen Oturum Sayısı: {report.sessions_analyzed}\n"
                      f"Rapor Tarihi: {report.created_at.strftime('%d.%m.%Y %H:%M')}")
        
        notes = ''  # İlerleme raporlarında not yok
        
        if format_type == 'txt':
            return _generate_txt(analysis_text, notes, file_name,
                                 report_type='İlerleyiş Analizi Raporu',
                                 client_name=client_name, counselor_name=counselor_name,
                                 extra_info=extra_info)
        elif format_type == 'pdf':
            return _generate_pdf(analysis_text, notes, file_name,
                                 report_type='İlerleyiş Analizi Raporu',
                                 client_name=client_name, counselor_name=counselor_name,
                                 extra_info=extra_info)
        elif format_type == 'docx':
            return _generate_docx(analysis_text, notes, file_name,
                                  report_type='İlerleyiş Analizi Raporu',
                                  client_name=client_name, counselor_name=counselor_name,
                                  extra_info=extra_info)
        else:
            abort(400)
    except Exception as e:
        import traceback
        print(f"İlerleme raporu indirme hatası: {traceback.format_exc()}")
        flash(f'Rapor indirilirken hata oluştu: {str(e)}', 'error')
        return redirect(url_for('main.view_progress_report', report_id=report_id))


def _generate_txt(analysis_text, notes, file_name, report_type, client_name, counselor_name, extra_info):
    """TXT formatında rapor oluştur"""
    import io
    content = f"PDR ANALİZ SİSTEMİ\n{report_type}\n\n"
    content += f"Danışan: {client_name}\n"
    content += f"Danışman: {counselor_name}\n"
    content += f"{extra_info}\n\n"
    content += "=" * 80 + "\n\n"
    content += analysis_text
    if notes:
        content += "\n\n" + "=" * 80 + "\n"
        content += "DANIŞMAN NOTLARI\n"
        content += "=" * 80 + "\n\n"
        content += notes
    content += "\n\n" + "=" * 80 + "\n"
    content += "Bu rapor PDR Analiz Sistemi tarafından otomatik olarak oluşturulmuştur.\n"
    
    buffer = io.BytesIO()
    buffer.write(content.encode('utf-8'))
    buffer.seek(0)
    return send_file(buffer, mimetype='text/plain; charset=utf-8',
                     as_attachment=True, download_name=f"{file_name}.txt")


def _generate_pdf(analysis_text, notes, file_name, report_type, client_name, counselor_name, extra_info):
    """PDF formatında rapor oluştur (fpdf2 ile)"""
    import io
    from fpdf import FPDF
    
    class PDFReport(FPDF):
        def header(self):
            self.set_font('Helvetica', 'B', 10)
            self.set_text_color(100, 100, 100)
            self.cell(0, 8, 'PDR Analiz Sistemi', align='R', new_x='LMARGIN', new_y='NEXT')
            self.line(10, self.get_y(), 200, self.get_y())
            self.ln(3)
        
        def footer(self):
            self.set_y(-15)
            self.set_font('Helvetica', 'I', 8)
            self.set_text_color(150, 150, 150)
            self.cell(0, 10, f'Sayfa {self.page_no()}/{{nb}}', align='C')
    
    pdf = PDFReport()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    
    # Başlık
    pdf.set_font('Helvetica', 'B', 18)
    pdf.set_text_color(21, 101, 192)
    pdf.cell(0, 12, 'PDR ANALIZ SISTEMI', align='C', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', 'B', 14)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 10, report_type, align='C', new_x='LMARGIN', new_y='NEXT')
    pdf.ln(5)
    
    # Bilgiler
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 6, f'Danisan: {client_name}  |  Danisman: {counselor_name}', align='C', new_x='LMARGIN', new_y='NEXT')
    for line in extra_info.split('\n'):
        pdf.cell(0, 6, line.strip(), align='C', new_x='LMARGIN', new_y='NEXT')
    pdf.ln(3)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    # Ana İçerik
    pdf.set_text_color(50, 50, 50)
    for line in analysis_text.split('\n'):
        stripped = line.strip()
        if not stripped:
            pdf.ln(3)
            continue
        # Başlık tespiti
        if stripped.startswith('## ') or stripped.startswith('# '):
            pdf.ln(3)
            pdf.set_font('Helvetica', 'B', 13)
            pdf.set_text_color(13, 110, 253)
            pdf.multi_cell(0, 7, stripped.lstrip('#').strip())
            pdf.set_text_color(50, 50, 50)
            pdf.ln(1)
        elif stripped.startswith('### '):
            pdf.ln(2)
            pdf.set_font('Helvetica', 'B', 11)
            pdf.set_text_color(73, 80, 87)
            pdf.multi_cell(0, 6, stripped.lstrip('#').strip())
            pdf.set_text_color(50, 50, 50)
            pdf.ln(1)
        elif stripped.startswith('- ') or stripped.startswith('* '):
            pdf.set_font('Helvetica', '', 10)
            pdf.cell(8, 6, chr(8226))  # bullet
            pdf.multi_cell(0, 6, stripped[2:])
        elif stripped.startswith('**') and stripped.endswith('**'):
            pdf.set_font('Helvetica', 'B', 10)
            pdf.multi_cell(0, 6, stripped.strip('*'))
            pdf.set_font('Helvetica', '', 10)
        else:
            pdf.set_font('Helvetica', '', 10)
            pdf.multi_cell(0, 6, stripped)
    
    # Danışman Notları
    if notes:
        pdf.ln(8)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)
        pdf.set_font('Helvetica', 'B', 13)
        pdf.set_text_color(21, 101, 192)
        pdf.cell(0, 8, 'Danisman Notlari', new_x='LMARGIN', new_y='NEXT')
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(50, 50, 50)
        pdf.ln(2)
        for line in notes.split('\n'):
            pdf.multi_cell(0, 6, line)
    
    # Alt Bilgi
    pdf.ln(10)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)
    pdf.set_font('Helvetica', 'I', 8)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 6, 'Bu rapor PDR Analiz Sistemi tarafindan otomatik olarak olusturulmustur.', align='C')
    
    buffer = io.BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return send_file(buffer, mimetype='application/pdf',
                     as_attachment=True, download_name=f"{file_name}.pdf")


def _generate_docx(analysis_text, notes, file_name, report_type, client_name, counselor_name, extra_info):
    """DOCX formatında rapor oluştur (python-docx ile)"""
    import io
    from docx import Document as DocxDocument
    from docx.shared import Pt, Inches, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    
    doc = DocxDocument()
    
    # Varsayılan stil
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Calibri'
    font.size = Pt(11)
    
    # Başlık
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run('PDR ANALİZ SİSTEMİ')
    run.bold = True
    run.font.size = Pt(18)
    run.font.color.rgb = RGBColor(21, 101, 192)
    
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(report_type)
    run.bold = True
    run.font.size = Pt(14)
    run.font.color.rgb = RGBColor(80, 80, 80)
    
    # Bilgi satırları
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(f'Danışan: {client_name}  |  Danışman: {counselor_name}')
    run.font.size = Pt(10)
    run.font.color.rgb = RGBColor(120, 120, 120)
    
    for line in extra_info.split('\n'):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(line.strip())
        run.font.size = Pt(10)
        run.font.color.rgb = RGBColor(120, 120, 120)
    
    doc.add_paragraph('_' * 80)
    
    # Ana İçerik
    for line in analysis_text.split('\n'):
        stripped = line.strip()
        if not stripped:
            doc.add_paragraph()
            continue
        
        if stripped.startswith('## ') or stripped.startswith('# '):
            p = doc.add_paragraph()
            run = p.add_run(stripped.lstrip('#').strip())
            run.bold = True
            run.font.size = Pt(14)
            run.font.color.rgb = RGBColor(13, 110, 253)
        elif stripped.startswith('### '):
            p = doc.add_paragraph()
            run = p.add_run(stripped.lstrip('#').strip())
            run.bold = True
            run.font.size = Pt(12)
            run.font.color.rgb = RGBColor(73, 80, 87)
        elif stripped.startswith('- ') or stripped.startswith('* ') or stripped.startswith('• '):
            doc.add_paragraph(stripped[2:], style='List Bullet')
        elif stripped.startswith('**') and stripped.endswith('**'):
            p = doc.add_paragraph()
            run = p.add_run(stripped.strip('*'))
            run.bold = True
        else:
            doc.add_paragraph(stripped)
    
    # Danışman Notları
    if notes:
        doc.add_paragraph('_' * 80)
        p = doc.add_paragraph()
        run = p.add_run('Danışman Notları')
        run.bold = True
        run.font.size = Pt(14)
        run.font.color.rgb = RGBColor(21, 101, 192)
        
        for line in notes.split('\n'):
            doc.add_paragraph(line)
    
    # Alt bilgi
    doc.add_paragraph('_' * 80)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run('Bu rapor PDR Analiz Sistemi tarafından otomatik olarak oluşturulmuştur.')
    run.italic = True
    run.font.size = Pt(9)
    run.font.color.rgb = RGBColor(150, 150, 150)
    
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return send_file(buffer, 
                     mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                     as_attachment=True, download_name=f"{file_name}.docx")


# ============================================================================
# ASENKRON ANALİZ - YENİ ENDPOINT'LER
# ============================================================================

@main_bp.route('/start_async_analysis/<int:session_id>', methods=['POST'])
@login_required
def start_async_analysis(session_id):
    """Video analizini arka planda başlat"""
    try:
        print(f"\n{'='*60}")
        print(f"🎬 Analiz başlatma isteği alındı - Session ID: {session_id}")
        print(f"{'='*60}")
        
        from app.celery_config import celery
        
        # Oturumu al ve yetki kontrolü
        session = Session.query.get_or_404(session_id)
        print(f"✅ Session bulundu: {session.title}")
        
        if session.client.counselor_id != current_user.id:
            print(f"❌ Yetki hatası - Oturum sahibi değil")
            abort(403)
        
        # Video dosyası kontrolü
        print(f"📹 Video path kontrolü: {session.video_path}")
        if not session.video_path:
            print(f"❌ Video path boş!")
            return jsonify({
                'status': 'error',
                'message': 'Video dosyası bulunamadı. Lütfen önce video yükleyin.'
            }), 400
        
        if not os.path.exists(session.video_path):
            print(f"❌ Video dosyası fiziksel olarak bulunamadı: {session.video_path}")
            return jsonify({
                'status': 'error',
                'message': f'Video dosyası bulunamadı: {session.video_path}'
            }), 400
        
        print(f"✅ Video dosyası mevcut: {session.video_path}")
        
        # Eğer zaten işlem devam ediyorsa
        if session.analysis_status == 'processing':
            print(f"⚠️ Analiz zaten devam ediyor")
            return jsonify({
                'status': 'warning',
                'message': 'Bu oturum için analiz zaten devam ediyor.',
                'progress': session.analysis_progress
            })
        
        # Celery task'ını başlat
        print(f"🚀 Celery task başlatılıyor...")
        from app.tasks import analyze_video
        task = analyze_video.apply_async(
            args=[session_id, current_user.id],
            countdown=1  # 1 saniye gecikme ile başlat (DB commit'in tamamlanması için)
        )
        print(f"✅ Celery task başlatıldı - Task ID: {task.id}")
        
        # Task ID'yi kaydet
        session.task_id = task.id
        session.analysis_status = 'processing'
        session.analysis_progress = 0
        db.session.commit()
        print(f"✅ Veritabanı güncellendi")
        
        print(f"{'='*60}\n")
        
        return jsonify({
            'status': 'success',
            'message': 'Video analizi arka planda başlatıldı. Analiz tamamlandığında bildirim alacaksınız.',
            'task_id': task.id,
            'session_id': session_id
        })
        
    except Exception as e:
        print(f"❌ Asenkron analiz başlatma hatası: {str(e)}")
        import traceback
        print(f"Traceback:\n{traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'message': f'Analiz başlatılırken hata oluştu: {str(e)}'
        }), 500


@main_bp.route('/check_analysis_status/<int:session_id>')
@login_required
def check_analysis_status(session_id):
    """Analiz durumunu kontrol et"""
    try:
        session = Session.query.get_or_404(session_id)
        if session.client.counselor_id != current_user.id:
            abort(403)
        
        return jsonify({
            'status': session.analysis_status,
            'progress': session.analysis_progress,
            'task_id': session.task_id,
            'has_results': bool(session.analysis_results)
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@main_bp.route('/check_progress_analysis_status/<int:progress_analysis_id>')
@login_required
def check_progress_analysis_status(progress_analysis_id):
    """İlerleyiş analizi durumunu kontrol et"""
    try:
        progress_analysis = ProgressAnalysis.query.get_or_404(progress_analysis_id)
        if progress_analysis.counselor_id != current_user.id:
            abort(403)
        
        return jsonify({
            'status': progress_analysis.analysis_status,
            'progress': progress_analysis.analysis_progress,
            'task_id': progress_analysis.task_id,
            'has_results': bool(progress_analysis.analysis_text)
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@main_bp.route('/cancel_analysis/<int:session_id>', methods=['POST'])
@login_required
def cancel_analysis(session_id):
    """Video analizini iptal et"""
    try:
        session = Session.query.get_or_404(session_id)
        if session.client.counselor_id != current_user.id:
            abort(403)
        if session.analysis_status != 'processing':
            return jsonify({
                'status': 'error',
                'message': 'İptal edilebilecek aktif bir analiz bulunmuyor.'
            }), 400
        task_id = session.task_id
        if not task_id:
            session.analysis_status = 'cancelled'
            session.task_id = None
            db.session.commit()
            return jsonify({'status': 'success', 'message': 'Analiz iptal edildi.'})
        from app.celery_config import celery
        celery.control.revoke(task_id, terminate=True, signal='SIGTERM')
        session.analysis_status = 'cancelled'
        session.task_id = None
        session.analysis_progress = 0
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Analiz iptal edildi.'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@main_bp.route('/cancel_progress_analysis/<int:progress_analysis_id>', methods=['POST'])
@login_required
def cancel_progress_analysis(progress_analysis_id):
    """İlerleyiş analizini iptal et"""
    try:
        progress_analysis = ProgressAnalysis.query.get_or_404(progress_analysis_id)
        if progress_analysis.counselor_id != current_user.id:
            abort(403)
        if progress_analysis.analysis_status not in ('processing', 'pending'):
            return jsonify({
                'status': 'error',
                'message': 'İptal edilebilecek aktif bir analiz bulunmuyor.'
            }), 400
        task_id = progress_analysis.task_id
        if task_id:
            from app.celery_config import celery
            celery.control.revoke(task_id, terminate=True, signal='SIGTERM')
        progress_analysis.analysis_status = 'cancelled'
        progress_analysis.task_id = None
        progress_analysis.analysis_progress = 0
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'İlerleyiş analizi iptal edildi.'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@main_bp.route('/notifications')
@login_required
def notifications():
    """Bildirimler sayfası"""
    try:
        # Kullanıcının tüm bildirimlerini al
        all_notifications = Notification.query.filter_by(
            counselor_id=current_user.id
        ).order_by(Notification.created_at.desc()).all()
        
        # Okunmamış sayısı
        unread_count = sum(1 for n in all_notifications if not n.is_read)
        
        return render_template('notifications.html',
                             notifications=all_notifications,
                             unread_count=unread_count)
    except Exception as e:
        print(f"Bildirimler sayfa hatası: {str(e)}")
        flash('Bildirimler yüklenirken hata oluştu.', 'error')
        return redirect(url_for('main.index'))


@main_bp.route('/get_notifications')
@login_required
def get_notifications():
    """Bildirimleri JSON olarak döndür (AJAX için)"""
    try:
        limit = request.args.get('limit', 10, type=int)
        
        notifications = Notification.query.filter_by(
            counselor_id=current_user.id
        ).order_by(Notification.created_at.desc()).limit(limit).all()
        
        unread_count = Notification.query.filter_by(
            counselor_id=current_user.id,
            is_read=False
        ).count()
        
        return jsonify({
            'notifications': [{
                'id': n.id,
                'title': n.title,
                'message': n.message,
                'type': n.notification_type,
                'is_read': n.is_read,
                'link': n.link.replace('/client/view_session/', '/session/view/') if n.link else '#',
                'created_at': n.created_at.strftime('%d.%m.%Y %H:%M'),
                'time_ago': get_time_ago(n.created_at)
            } for n in notifications],
            'unread_count': unread_count
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@main_bp.route('/mark_notification_read/<int:notification_id>', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    """Bildirimi okundu olarak işaretle"""
    try:
        notification = Notification.query.get_or_404(notification_id)
        
        # Yetki kontrolü
        if notification.counselor_id != current_user.id:
            abort(403)
        
        notification.is_read = True
        db.session.commit()
        
        return jsonify({'status': 'success'})
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@main_bp.route('/mark_all_notifications_read', methods=['POST'])
@login_required
def mark_all_notifications_read():
    """Tüm bildirimleri okundu olarak işaretle"""
    try:
        Notification.query.filter_by(
            counselor_id=current_user.id,
            is_read=False
        ).update({'is_read': True})
        
        db.session.commit()
        
        return jsonify({'status': 'success'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@main_bp.route('/delete_notification/<int:notification_id>', methods=['POST'])
@login_required
def delete_notification(notification_id):
    """Bildirimi sil"""
    try:
        notification = Notification.query.get_or_404(notification_id)
        
        # Yetki kontrolü
        if notification.counselor_id != current_user.id:
            abort(403)
        
        db.session.delete(notification)
        db.session.commit()
        
        flash('Bildirim silindi.', 'success')
        return redirect(url_for('main.notifications'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Bildirim silinirken hata oluştu: {str(e)}', 'error')
        return redirect(url_for('main.notifications'))


def get_time_ago(dt):
    """Zamanı 'X dakika önce' formatında döndür"""
    from datetime import datetime, timedelta
    
    now = datetime.utcnow()
    diff = now - dt
    
    if diff < timedelta(minutes=1):
        return 'Az önce'
    elif diff < timedelta(hours=1):
        mins = int(diff.total_seconds() / 60)
        return f'{mins} dakika önce'
    elif diff < timedelta(days=1):
        hours = int(diff.total_seconds() / 3600)
        return f'{hours} saat önce'
    elif diff < timedelta(days=7):
        days = diff.days
        return f'{days} gün önce'
    else:
        return dt.strftime('%d.%m.%Y')


# ============================================================================
# VIDEO YÜKLEME VE YÖNETİMİ
# ============================================================================

@main_bp.route('/upload_session_video/<int:session_id>', methods=['POST'])
@login_required
def upload_session_video(session_id):
    """Oturuma video yükle"""
    try:
        session = Session.query.get_or_404(session_id)
        
        # Yetki kontrolü
        if session.client.counselor_id != current_user.id:
            abort(403)
        
        # Video dosyasını al
        if 'video' not in request.files:
            return jsonify({'status': 'error', 'message': 'Video dosyası bulunamadı'}), 400
        
        video_file = request.files['video']
        
        if video_file.filename == '':
            return jsonify({'status': 'error', 'message': 'Dosya seçilmedi'}), 400
        
        # Analiz devam ediyorsa yüklemeyi engelle
        if session.analysis_status == 'processing':
            return jsonify({
                'status': 'error',
                'message': 'Analiz devam ederken yeni video yüklenemez. Lütfen analizin bitmesini bekleyin.'
            }), 400
        
        # Dosya uzantısını kontrol et
        allowed_extensions = {'mp4', 'avi', 'mov', 'mkv', 'webm', 'flv', 'wmv'}
        file_ext = video_file.filename.rsplit('.', 1)[1].lower() if '.' in video_file.filename else ''
        
        if file_ext not in allowed_extensions:
            return jsonify({
                'status': 'error', 
                'message': f'Geçersiz dosya formatı. İzin verilen formatlar: {", ".join(allowed_extensions)}'
            }), 400
        
        # Eski video varsa sil
        if session.video_path and os.path.exists(session.video_path):
            try:
                os.remove(session.video_path)
                print(f"🗑️ Eski video silindi: {session.video_path}")
            except Exception as e:
                print(f"⚠️ Eski video silinemedi: {str(e)}")
        
        # FileHandler ile videoyu kaydet
        file_handler = FileHandler()
        
        # Güvenli dosya adı oluştur
        safe_filename = secure_filename(f"session_{session_id}_{int(time.time())}.{file_ext}")
        video_path = os.path.join(file_handler.video_folder, safe_filename)
        
        # Videoyu kaydet
        video_file.save(video_path)
        
        # Video path'i veritabanına kaydet
        session.video_path = video_path
        
        # Analiz durumunu sıfırla (yeni video yüklendiği için)
        session.analysis_status = 'pending'
        session.analysis_progress = 0
        session.analysis_results = None
        session.task_id = None
        
        db.session.commit()
        
        print(f"✅ Video başarıyla yüklendi: {video_path}")
        
        return jsonify({
            'status': 'success',
            'message': 'Video başarıyla yüklendi',
            'video_path': video_path
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Video yükleme hatası: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@main_bp.route('/delete_session_video/<int:session_id>', methods=['POST'])
@login_required
def delete_session_video(session_id):
    """Oturumdaki videoyu sil"""
    try:
        session = Session.query.get_or_404(session_id)
        
        # Yetki kontrolü
        if session.client.counselor_id != current_user.id:
            abort(403)
        
        # Analiz devam ediyorsa silmeyi engelle
        if session.analysis_status == 'processing':
            return jsonify({
                'status': 'error',
                'message': 'Analiz devam ederken video silinemez. Lütfen analizin bitmesini bekleyin.'
            }), 400
        
        # Video yoksa
        if not session.video_path:
            return jsonify({'status': 'error', 'message': 'Bu oturumda video bulunmuyor'}), 400
        
        # Video dosyasını sil
        if os.path.exists(session.video_path):
            try:
                os.remove(session.video_path)
                print(f"🗑️ Video silindi: {session.video_path}")
            except Exception as e:
                print(f"⚠️ Video dosyası silinemedi: {str(e)}")
        
        # Veritabanından video path'ini ve analiz sonuçlarını temizle
        session.video_path = None
        session.analysis_status = 'pending'
        session.analysis_progress = 0
        session.analysis_results = None
        session.task_id = None
        
        # İlişkili AI analizlerini de sil
        AIAnalysis.query.filter_by(session_id=session_id).delete()
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Video başarıyla silindi'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Video silme hatası: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ============================================================================
# ADMIN ROUTES - Sadece admin kullanıcılar erişebilir
# ============================================================================

from app.utils.decorators import admin_required
from datetime import timedelta

@main_bp.route('/admin/user-activities')
@login_required
@admin_required
def admin_user_activities():
    """Tüm kullanıcıların aktivitelerini göster (Sadece Admin)"""
    # Filtreler
    date_filter = request.args.get('date', 'week')
    user_id = request.args.get('user_id', type=int)
    action_filter = request.args.get('action', '')
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    # Base query
    query = UserActivity.query
    
    # Kullanıcı filtresi
    if user_id:
        query = query.filter_by(counselor_id=user_id)
    
    # Tarih filtresi
    if date_filter == 'today':
        today = get_turkey_time().date()
        query = query.filter(db.func.date(UserActivity.created_at) == today)
    elif date_filter == 'week':
        week_ago = get_turkey_time() - timedelta(days=7)
        query = query.filter(UserActivity.created_at >= week_ago)
    elif date_filter == 'month':
        month_ago = get_turkey_time() - timedelta(days=30)
        query = query.filter(UserActivity.created_at >= month_ago)
    
    # Action filtresi
    if action_filter:
        query = query.filter(UserActivity.action.like(f'%{action_filter}%'))
    
    # Paginate
    activities = query.order_by(UserActivity.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Tüm kullanıcılar (dropdown için)
    all_users = Counselor.query.order_by(Counselor.name).all()
    
    # İstatistikler
    stats = {
        'total_activities': query.count(),
        'unique_users': db.session.query(UserActivity.counselor_id).distinct().count(),
        'today_activities': UserActivity.query.filter(
            db.func.date(UserActivity.created_at) == get_turkey_time().date()
        ).count()
    }
    
    return render_template('admin/user_activities.html', 
                         activities=activities,
                         all_users=all_users,
                         stats=stats,
                         date_filter=date_filter,
                         selected_user_id=user_id,
                         action_filter=action_filter)


@main_bp.route('/admin/manage-users')
@login_required
@admin_required
def manage_users():
    """Kullanıcı yönetimi - Admin yetkisi ver/al"""
    users = Counselor.query.order_by(Counselor.created_at.desc()).all()
    return render_template('admin/manage_users.html', users=users)


@main_bp.route('/admin/toggle-admin/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def toggle_admin(user_id):
    """Kullanıcının admin yetkisini aç/kapat"""
    from app.utils.activity import log_activity
    
    user = Counselor.query.get_or_404(user_id)
    
    # Kendini admin'likten çıkaramaz
    if user.id == current_user.id:
        flash('Kendi admin yetkinizi kaldıramazsınız!', 'danger')
        return redirect(url_for('main.manage_users'))
    
    user.is_admin = not user.is_admin
    db.session.commit()
    
    status = 'verildi' if user.is_admin else 'kaldırıldı'
    flash(f'{user.name} kullanıcısının admin yetkisi {status}.', 'success')
    log_activity('toggle_admin', f'{user.name} kullanıcısının admin yetkisi {status}')
    
    return redirect(url_for('main.manage_users'))