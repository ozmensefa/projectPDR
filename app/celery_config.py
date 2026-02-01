# -*- coding: utf-8 -*-
"""
Celery Konfigürasyonu - Asenkron Task Queue
"""
import os
from celery import Celery
from app.config import Config

def make_celery(app=None):
    """Celery instance oluştur"""
    # Redis URL'ini al
    redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    
    celery = Celery(
        'pdr_tasks',
        broker=redis_url,
        backend=redis_url,
        include=['app.tasks']
    )
    
    # Celery konfigürasyonu
    celery.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='Europe/Istanbul',
        enable_utc=True,
        task_track_started=True,
        task_time_limit=7200,  # 2 saat max (daha uzun analizler için)
        task_soft_time_limit=6900,  # 1 saat 55 dakika soft limit
        worker_prefetch_multiplier=1,
        worker_max_tasks_per_child=50,
        task_acks_late=True,
        task_reject_on_worker_lost=True,
        result_expires=3600,  # Sonuçlar 1 saat sonra silinir
        broker_connection_retry_on_startup=True,  # Başlangıçta bağlantı hatası varsa tekrar dene
        worker_send_task_events=True,  # Task event'lerini gönder
        task_send_sent_event=True,  # Task gönderildiğinde event gönder
    )
    
    if app:
        celery.conf.update(app.config)
        
        class ContextTask(celery.Task):
            def __call__(self, *args, **kwargs):
                with app.app_context():
                    return self.run(*args, **kwargs)
        
        celery.Task = ContextTask
    
    return celery

# Celery instance
celery = make_celery()

