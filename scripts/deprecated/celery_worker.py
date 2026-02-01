# -*- coding: utf-8 -*-
"""
Celery Worker Başlatma Modülü
Bu dosya Celery worker'ını başlatmak için kullanılır
"""

from app import create_app
from app.celery_config import make_celery

# Flask app oluştur
app = create_app()

# Celery instance'ı Flask app context'i ile oluştur
celery = make_celery(app)

if __name__ == '__main__':
    # Worker'ı başlat
    celery.start()

