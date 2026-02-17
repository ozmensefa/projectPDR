# -*- coding: utf-8 -*-
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from app.config import Config
import os
import markdown

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Lütfen giriş yapın.'

def create_app():
    # Absolute path to the template and static folders
    template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates'))
    static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'static'))
    
    app = Flask(__name__,
                template_folder=template_dir,
                static_folder=static_dir)
    
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    
    # Celery'yi initialize et
    from app.celery_config import make_celery
    celery = make_celery(app)
    app.celery = celery

    # Markdown filtresi ekle
    app.jinja_env.filters['markdown'] = lambda text: markdown.markdown(text) if text else ''

    # Tarih filtresi ekle
    @app.template_filter('friendly_date')
    def friendly_date(date):
        """Tarihi kullanıcı dostu formatta göster"""
        from datetime import datetime
        
        if not date:
            return '-'
        
        now = datetime.now()
        today = now.date()
        date_only = date.date()
        
        # Tarih farkını hesapla
        diff = (date_only - today).days
        
        if diff == 0:
            return f"Bugün {date.strftime('%H:%M')}"
        elif diff == -1:
            return f"Dün {date.strftime('%H:%M')}"
        elif diff == 1:
            return f"Yarın {date.strftime('%H:%M')}"
        elif -7 <= diff < 0:
            days = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi', 'Pazar']
            return f"Geçen {days[date.weekday()]} {date.strftime('%H:%M')}"
        elif 0 < diff <= 7:
            days = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi', 'Pazar']
            return f"{days[date.weekday()]} {date.strftime('%H:%M')}"
        else:
            return date.strftime('%d.%m.%Y %H:%M')

    # Blueprint'leri kaydet
    from app.routes import main_bp
    from app.auth import auth_bp
    from app.client import client_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(client_bp)

    # with app.app_context():
    #     db.create_all()  # Sadece ilk kurulumda gerekli

    return app 

@login_manager.user_loader
def load_user(id):
    from app.models import Counselor
    from app.database_utils import safe_db_query
    
    def query_user():
        return Counselor.query.get(int(id))
    
    user = safe_db_query(query_user, None)
    
    if user is None:
        print(f"⚠️ Kullanıcı bulunamadı veya veritabanı hatası (ID: {id})")
    
    return user 