# -*- coding: utf-8 -*-
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'gizli-anahtar-buraya'
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
    TEMP_FOLDER = os.path.join(os.getcwd(), 'temp_files')
    
    # Gemini API Key - Sabit olarak tanımlandı
    GEMINI_API_KEY = 'AIzaSyD8IjMxkJqWIdJZrRjz_AirKOhcvfEBkFs'
    
    # SQLAlchemy ayarları - Geliştirilmiş SQLite konfigürasyonu
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
    
    # Dosya yükleme ayarları
    MAX_CONTENT_LENGTH = 1 * 1024 * 1024 * 1024  # 1GB max-size
    ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'wmv'}

    # Klasörleri oluştur
    for folder in [UPLOAD_FOLDER, TEMP_FOLDER]:
        if not os.path.exists(folder):
            os.makedirs(folder)
    
    @classmethod
    def validate_gemini_api_key(cls):
        """Gemini API key'ini doğrula"""
        if not cls.GEMINI_API_KEY:
            return False, "API key bulunamadı"
        
        if len(cls.GEMINI_API_KEY) < 30:
            return False, "API key çok kısa"
        
        if not cls.GEMINI_API_KEY.startswith('AIzaSy'):
            return False, "API key formatı yanlış (AIzaSy ile başlamalı)"
        
        return True, "Geçerli" 