# -*- coding: utf-8 -*-
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'gizli-anahtar-buraya')
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
    TEMP_FOLDER = os.path.join(os.getcwd(), 'temp_files')
    
    # Gemini API - Oturum ve İlerleyiş analizi için ayrı anahtarlar
    GEMINI_API_KEY_SESSION = os.environ.get('GEMINI_API_KEY_SESSION', '')
    GEMINI_API_KEY_PROGRESS = os.environ.get('GEMINI_API_KEY_PROGRESS', '')
    GEMINI_MAX_OUTPUT_TOKENS = int(os.environ.get('GEMINI_MAX_OUTPUT_TOKENS', '65536'))
    
    # SQLAlchemy ayarları
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.getcwd(), 'instance', 'app.db') + '?timeout=20'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_timeout': 20,
        'pool_recycle': 300,
        'pool_pre_ping': True,
        'connect_args': {
            'timeout': 20,
            'check_same_thread': False,
            'isolation_level': None
        }
    }
    
    # Resend E-posta
    RESEND_API_KEY = os.environ.get('RESEND_API_KEY', '')
    RESEND_FROM_EMAIL = 'YAKADES Analiz <noreply@yakades.com.tr>'
    SITE_URL = 'https://yakades.com.tr'
    
    # Dosya yükleme ayarları
    MAX_CONTENT_LENGTH = int(2.5 * 1024 * 1024 * 1024)  # 2.5GB max-size
    ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'wmv'}

    # Analiz süre tahminleri (dakika)
    VIDEO_ANALYSIS_ESTIMATE_MIN = 10
    VIDEO_ANALYSIS_ESTIMATE_MAX = 15
    PROGRESS_ANALYSIS_BASE_MIN = 5
    PROGRESS_ANALYSIS_BASE_MAX = 10
    PROGRESS_ANALYSIS_PER_SESSION_MIN = 2
    PROGRESS_ANALYSIS_PER_SESSION_MAX = 4

    # Klasörleri oluştur
    for folder in [UPLOAD_FOLDER, TEMP_FOLDER]:
        if not os.path.exists(folder):
            os.makedirs(folder)
    
    @classmethod
    def validate_gemini_api_key(cls, key_type='session'):
        """Gemini API key'ini doğrula
        
        Args:
            key_type: 'session' veya 'progress'
        """
        key = cls.GEMINI_API_KEY_SESSION if key_type == 'session' else cls.GEMINI_API_KEY_PROGRESS
        label = 'Oturum' if key_type == 'session' else 'İlerleyiş'
        
        if not key:
            return False, f"{label} API key bulunamadı"
        
        if len(key) < 30:
            return False, f"{label} API key çok kısa"
        
        if not key.startswith('AIzaSy'):
            return False, f"{label} API key formatı yanlış (AIzaSy ile başlamalı)"
        
        return True, "Geçerli" 