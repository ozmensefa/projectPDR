# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, redirect, url_for, flash, abort, current_app
from flask_login import login_required, current_user
from app.models import Client, Session, AIAnalysis
from app.forms import ClientForm, SessionForm
from app import db
import os
import uuid
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta

client_bp = Blueprint('client', __name__)

def save_photo(photo, client_id):
    """Danışan fotoğrafını kaydet"""
    if photo and photo.filename:
        # Güvenli dosya adı oluştur
        filename = secure_filename(photo.filename)
        # Benzersiz dosya adı için UUID ekle
        name, ext = os.path.splitext(filename)
        unique_filename = f"client_{client_id}_{uuid.uuid4().hex[:8]}{ext}"
        
        # Upload klasörünü oluştur
        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'client_photos')
        os.makedirs(upload_folder, exist_ok=True)
        
        # Dosyayı kaydet
        photo_path = os.path.join(upload_folder, unique_filename)
        photo.save(photo_path)
        
        return unique_filename
    return None

def delete_photo(filename):
    """Eski fotoğrafı sil"""
    if filename:
        photo_path = os.path.join(current_app.root_path, 'static', 'uploads', 'client_photos', filename)
        if os.path.exists(photo_path):
            os.remove(photo_path)

def generate_client_suggestions(client):
    """Danışan durumuna göre öneriler oluştur"""
    suggestions = []
    now = datetime.now()
    
    # Oturum sayısı kontrolü
    session_count = len(client.sessions)
    if session_count == 0:
        suggestions.append({
            'type': 'info',
            'icon': 'fas fa-calendar-plus',
            'title': 'İlk Oturumu Planlayın',
            'description': 'Bu danışan için henüz oturum kaydı bulunmuyor. İlk oturumu planlayarak sürece başlayın.',
            'action': 'Oturum Ekle',
            'url': 'client.add_session',
            'client_id': client.id
        })
    elif session_count < 3:
        suggestions.append({
            'type': 'tip',
            'icon': 'fas fa-calendar-check',
            'title': 'Daha Fazla Oturum Planlayın',
            'description': f'Bu danışanla {session_count} oturum gerçekleştirildi. Süreklilik için daha fazla oturum planlayabilirsiniz.',
            'action': 'Oturum Ekle',
            'url': 'client.add_session',
            'client_id': client.id
        })
    
    # Analiz edilmemiş oturumlar kontrolü
    unanalyzed_sessions = [s for s in client.sessions if not s.analysis_results]
    if unanalyzed_sessions:
        suggestions.append({
            'type': 'warning',
            'icon': 'fas fa-brain',
            'title': 'Analiz Bekleyen Oturumlar',
            'description': f'{len(unanalyzed_sessions)} oturum analiz bekliyor. Oturum sayfasından analiz başlatabilirsiniz.',
            'action': 'Danışanlara Git',
            'url': 'client.list_clients'
        })
    
    # Son oturum tarihi kontrolü
    if client.sessions:
        last_session = max(client.sessions, key=lambda x: x.date)
        days_since_last = (now - last_session.date).days
        
        if days_since_last > 30:
            suggestions.append({
                'type': 'primary',
                'icon': 'fas fa-clock',
                'title': 'Uzun Süredir Oturum Yok',
                'description': f'Son oturum {days_since_last} gün önce gerçekleştirildi. Danışanla iletişime geçmeyi düşünebilirsiniz.',
                'action': 'Yeni Oturum',
                'url': 'client.add_session',
                'client_id': client.id
            })
    
    # İlerleyiş analizi kontrolü
    if len(client.progress_analyses) == 0 and session_count >= 2:
        suggestions.append({
            'type': 'success',
            'icon': 'fas fa-chart-line',
            'title': 'İlk İlerleyiş Analizinizi Oluşturun',
            'description': 'Danışanın gelişimini değerlendirmek için ilerleyiş analizi oluşturabilirsiniz.',
            'action': 'Analiz Oluştur',
            'url': 'main.progress_analysis',
            'client_id': client.id
        })
    
    # Hiç öneri yoksa, pozitif bir mesaj göster
    if not suggestions:
        suggestions.append({
            'type': 'success',
            'icon': 'fas fa-check-circle',
            'title': 'Her Şey Yolunda!',
            'description': 'Bu danışan için şimdilik her şey iyi gidiyor. Herhangi bir acil öneri bulunmamaktadır.'
        })
    
    return suggestions[:4]  # Maksimum 4 öneri göster

@client_bp.route('/clients')
@login_required
def list_clients():
    clients = Client.query.filter_by(counselor_id=current_user.id).all()
    return render_template('client/list.html', clients=clients)

@client_bp.route('/client/add', methods=['GET', 'POST'])
@login_required
def add_client():
    form = ClientForm()
    if form.validate_on_submit():
        client = Client(
            name=form.name.data,
            age=form.age.data,
            gender=form.gender.data,
            contact=form.contact.data,
            notes=form.notes.data,
            counselor_id=current_user.id
        )
        db.session.add(client)
        db.session.flush()  # ID'yi almak için flush
        
        # Fotoğraf varsa kaydet
        if form.photo.data:
            photo_filename = save_photo(form.photo.data, client.id)
            client.photo_filename = photo_filename
        
        db.session.commit()
        flash('Danışan başarıyla eklendi.')
        return redirect(url_for('client.view_client', client_id=client.id))
    return render_template('client/add.html', form=form)

@client_bp.route('/client/<int:client_id>')
@login_required
def view_client(client_id):
    client = Client.query.get_or_404(client_id)
    if client.counselor_id != current_user.id:
        abort(403)
    
    # Danışan-specific öneriler oluştur
    suggestions = generate_client_suggestions(client)
    
    return render_template('client/view.html', client=client, suggestions=suggestions)

@client_bp.route('/client/<int:client_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_client(client_id):
    client = Client.query.get_or_404(client_id)
    if client.counselor_id != current_user.id:
        abort(403)
    
    form = ClientForm(obj=client)
    if form.validate_on_submit():
        # Eski fotoğraf bilgisini sakla
        old_photo = client.photo_filename
        
        # Form verilerini güncelle (fotoğraf hariç)
        client.name = form.name.data
        client.age = form.age.data
        client.gender = form.gender.data
        client.contact = form.contact.data
        client.notes = form.notes.data
        
        # Eğer yeni fotoğraf yüklendiyse
        if form.photo.data:
            # Eski fotoğrafı sil
            if old_photo:
                delete_photo(old_photo)
            # Yeni fotoğrafı kaydet
            photo_filename = save_photo(form.photo.data, client.id)
            client.photo_filename = photo_filename
        
        db.session.commit()
        flash('Danışan bilgileri güncellendi.')
        return redirect(url_for('client.view_client', client_id=client.id))
    
    return render_template('client/edit.html', form=form, client=client)

@client_bp.route('/client/<int:client_id>/session/add', methods=['GET', 'POST'])
@login_required
def add_session(client_id):
    client = Client.query.get_or_404(client_id)
    if client.counselor_id != current_user.id:
        abort(403)
    
    form = SessionForm()
    if form.validate_on_submit():
        session = Session(
            title=form.title.data,
            date=form.session_date.data,
            notes=form.notes.data,
            client_id=client.id
        )
        db.session.add(session)
        db.session.commit()
        flash('Oturum başarıyla eklendi.')
        return redirect(url_for('client.view_client', client_id=client.id))
    
    return render_template('client/add_session.html', form=form, client=client)

@client_bp.route('/session/view/<int:session_id>')
@login_required
def view_session(session_id):
    session = Session.query.get_or_404(session_id)
    if session.client.counselor_id != current_user.id:
        abort(403)
    
    # Kaydedilmiş AI analizini al
    saved_analysis = AIAnalysis.query.filter_by(
        session_id=session_id
    ).first()
    
    return render_template(
        'client/view_session.html', 
        client=session.client, 
        session=session,
        saved_analysis=saved_analysis
    )

@client_bp.route('/session/<int:session_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_session(session_id):
    session = Session.query.get_or_404(session_id)
    if session.client.counselor_id != current_user.id:
        abort(403)
    
    form = SessionForm(obj=session)
    # Tarih alanını manuel olarak set et çünkü obj=session ile otomatik mapping çalışmayabilir
    if not form.session_date.data:
        form.session_date.data = session.date
        
    if form.validate_on_submit():
        session.title = form.title.data
        session.date = form.session_date.data
        session.notes = form.notes.data
        db.session.commit()
        flash('Oturum bilgileri güncellendi.')
        return redirect(url_for('client.view_session', session_id=session.id))
    
    return render_template('client/edit_session.html', form=form, session=session)



@client_bp.route('/session/<int:session_id>/delete', methods=['POST'])
@login_required
def delete_session(session_id):
    session = Session.query.get_or_404(session_id)
    
    # Yetki kontrolü
    if session.client.counselor_id != current_user.id:
        abort(403)
    
    try:
        # Oturumda rapor var mı kontrol et
        if session.analysis_results or session.ai_analyses:
            flash('Oturumda rapor bulunduğu için silme işlemi yapılamaz.', 'warning')
            return redirect(url_for('client.view_client', client_id=session.client_id))
        
        # Video dosyası varsa sil
        if session.video_path and os.path.exists(session.video_path):
            os.remove(session.video_path)
        
        # Oturumu veritabanından sil
        client_id = session.client_id
        db.session.delete(session)
        db.session.commit()
        
        flash('Oturum başarıyla silindi.', 'success')
        return redirect(url_for('client.view_client', client_id=client_id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Oturum silinirken bir hata oluştu: {str(e)}', 'danger')
        return redirect(url_for('client.view_client', client_id=session.client_id))

@client_bp.route('/session/<int:session_id>/delete_analysis', methods=['POST'])
@login_required
def delete_session_analysis(session_id):
    session = Session.query.get_or_404(session_id)
    
    # Yetki kontrolü
    if session.client.counselor_id != current_user.id:
        abort(403)
    
    try:
        # Analiz sonuçlarını sil
        session.analysis_results = None
        db.session.commit()
        
        flash('Oturum analizi başarıyla silindi.', 'success')
        return redirect(url_for('client.view_session', session_id=session_id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Analiz silinirken bir hata oluştu: {str(e)}', 'danger')
        return redirect(url_for('client.view_session', session_id=session_id))

@client_bp.route('/client/<int:client_id>/delete', methods=['POST'])
@login_required
def delete_client(client_id):
    client = Client.query.get_or_404(client_id)
    
    # Yetki kontrolü
    if client.counselor_id != current_user.id:
        abort(403)
    
    try:
        # İlişkili verileri kontrol et
        session_count = len(client.sessions)
        progress_count = len(client.progress_analyses)
        
        # Uyarı mesajı hazırla
        warning_msg = f"Bu danışanla ilgili {session_count} oturum"
        if progress_count > 0:
            warning_msg += f" ve {progress_count} ilerleme raporu"
        warning_msg += " bulunmaktadır. Danışan silindiğinde tüm bu veriler kalıcı olarak silinecektir."
        
        # Eğer veri varsa, onay kontrolü yap (normalde JS ile yapılır)
        if session_count > 0 or progress_count > 0:
            flash(warning_msg, 'warning')
        
        # Tüm ilişkili oturumlardaki video dosyalarını sil
        for session in client.sessions:
            if session.video_path and os.path.exists(session.video_path):
                os.remove(session.video_path)
        
        # İlişkili AI analizlerini sil
        for session in client.sessions:
            AIAnalysis.query.filter_by(session_id=session.id).delete()
        
        # İlişkili oturumları sil
        Session.query.filter_by(client_id=client.id).delete()
        
        # İlişkili ilerleme analizlerini sil
        from app.models import ProgressAnalysis
        ProgressAnalysis.query.filter_by(client_id=client.id).delete()
        
        # Danışan fotoğrafını sil
        if client.photo_filename:
            delete_photo(client.photo_filename)
        
        # Danışanı sil
        db.session.delete(client)
        db.session.commit()
        
        flash(f'{client.name} adlı danışan ve tüm ilişkili verileri başarıyla silindi.', 'success')
        return redirect(url_for('client.list_clients'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Danışan silinirken bir hata oluştu: {str(e)}', 'danger')
        return redirect(url_for('client.list_clients')) 