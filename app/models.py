# -*- coding: utf-8 -*-
from flask_login import UserMixin
from datetime import datetime, timedelta
from app import db

def get_turkey_time():
    """Türkiye saatini döndür (UTC+3)"""
    return datetime.utcnow() + timedelta(hours=3)

class Counselor(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(100))
    photo_filename = db.Column(db.String(100), nullable=True)  # Profil fotoğrafı
    is_admin = db.Column(db.Boolean, default=False)  # Admin yetkisi
    created_at = db.Column(db.DateTime, default=get_turkey_time)
    clients = db.relationship('Client', backref='counselor', lazy=True)

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    contact = db.Column(db.String(100))
    notes = db.Column(db.Text)
    photo_filename = db.Column(db.String(100), nullable=True)  # Fotoğraf dosya adı
    created_at = db.Column(db.DateTime, default=get_turkey_time)
    counselor_id = db.Column(db.Integer, db.ForeignKey('counselor.id'), nullable=False)
    sessions = db.relationship('Session', backref='client', lazy=True)

class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, default=get_turkey_time)
    notes = db.Column(db.Text)
    video_path = db.Column(db.String(255))
    analysis_results = db.Column(db.Text, nullable=True, default=None)
    analysis_status = db.Column(db.String(20), default='pending')  # pending, processing, completed, failed
    analysis_progress = db.Column(db.Integer, default=0)  # 0-100 arası ilerleme yüzdesi
    task_id = db.Column(db.String(100), nullable=True)  # Celery task ID
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)

    def __init__(self, **kwargs):
        # analysis_results parametresi gelmezse, hiç set etme (None default olacak)
        if 'analysis_status' not in kwargs:
            kwargs['analysis_status'] = 'pending'
        if 'analysis_progress' not in kwargs:
            kwargs['analysis_progress'] = 0
        super(Session, self).__init__(**kwargs)

class AIAnalysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('counselor.id'), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('session.id'), nullable=False)
    analysis_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=get_turkey_time)
    
    user = db.relationship('Counselor', backref=db.backref('ai_analyses', lazy=True))
    session = db.relationship('Session', backref=db.backref('ai_analyses', lazy=True))

class ProgressAnalysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    counselor_id = db.Column(db.Integer, db.ForeignKey('counselor.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    start_session_id = db.Column(db.Integer, db.ForeignKey('session.id'), nullable=False)
    end_session_id = db.Column(db.Integer, db.ForeignKey('session.id'), nullable=False)
    analysis_text = db.Column(db.Text, nullable=True, default=None)  # Analiz tamamlanana kadar None
    sessions_analyzed = db.Column(db.Integer, nullable=False)  # Analiz edilen oturum sayısı
    date_range = db.Column(db.String(100), nullable=False)  # "01.01.2024 - 15.01.2024" formatı
    analysis_status = db.Column(db.String(20), default='pending')  # pending, processing, completed, failed
    analysis_progress = db.Column(db.Integer, default=0)  # 0-100 arası ilerleme yüzdesi
    task_id = db.Column(db.String(100), nullable=True)  # Celery task ID
    created_at = db.Column(db.DateTime, default=get_turkey_time)
    
    counselor = db.relationship('Counselor', backref=db.backref('progress_analyses', lazy=True))
    client = db.relationship('Client', backref=db.backref('progress_analyses', lazy=True))
    start_session = db.relationship('Session', foreign_keys=[start_session_id])
    end_session = db.relationship('Session', foreign_keys=[end_session_id])
    
    def __init__(self, **kwargs):
        # analysis_text parametresi gelmezse, hiç set etme (None default olacak)
        if 'analysis_status' not in kwargs:
            kwargs['analysis_status'] = 'pending'
        if 'analysis_progress' not in kwargs:
            kwargs['analysis_progress'] = 0
        super(ProgressAnalysis, self).__init__(**kwargs)

class Notification(db.Model):
    """Kullanıcı bildirimleri için model"""
    id = db.Column(db.Integer, primary_key=True)
    counselor_id = db.Column(db.Integer, db.ForeignKey('counselor.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50), default='info')  # info, success, warning, error
    is_read = db.Column(db.Boolean, default=False)
    link = db.Column(db.String(500), nullable=True)  # Bildirimin yönlendireceği link
    related_session_id = db.Column(db.Integer, db.ForeignKey('session.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=get_turkey_time)
    
    counselor = db.relationship('Counselor', backref=db.backref('notifications', lazy=True, order_by='Notification.created_at.desc()'))
    session = db.relationship('Session', backref=db.backref('notifications', lazy=True))

class UserActivity(db.Model):
    """Kullanıcı aktivite kayıtları"""
    __tablename__ = 'user_activity'
    
    id = db.Column(db.Integer, primary_key=True)
    counselor_id = db.Column(db.Integer, db.ForeignKey('counselor.id'), nullable=False)
    
    # Ne yaptı?
    action = db.Column(db.String(100), nullable=False)  # 'login', 'add_client', 'view_session', vb.
    description = db.Column(db.String(500))  # Detaylı açıklama
    
    # Ne zaman?
    created_at = db.Column(db.DateTime, default=get_turkey_time, index=True)
    
    # İlişki
    counselor = db.relationship('Counselor', backref=db.backref('activities', lazy='dynamic', order_by='UserActivity.created_at.desc()'))
    
    def __repr__(self):
        return f'<UserActivity {self.counselor.name}: {self.action}>'