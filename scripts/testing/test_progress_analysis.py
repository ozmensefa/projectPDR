#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
İlerleyiş Analizi Test Script
Bu script ile ilerleyiş analizi durumunu kontrol edebilirsiniz.
"""
from app import create_app, db
from app.models import ProgressAnalysis, Client

def show_progress_analyses():
    """Tüm ilerleyiş analizlerini göster"""
    app = create_app()
    with app.app_context():
        analyses = ProgressAnalysis.query.order_by(ProgressAnalysis.id.desc()).all()
        
        if not analyses:
            print("❌ Hiç ilerleyiş analizi bulunamadı.")
            return
        
        print(f"\n{'='*80}")
        print(f"📊 TOPLAM {len(analyses)} İLERLEYİŞ ANALİZİ")
        print(f"{'='*80}\n")
        
        for a in analyses:
            # Status icon
            if a.analysis_status == 'completed':
                icon = '✅'
            elif a.analysis_status == 'processing':
                icon = '⏳'
            elif a.analysis_status == 'pending':
                icon = '🔵'
            elif a.analysis_status == 'failed':
                icon = '❌'
            else:
                icon = '❓'
            
            print(f"{icon} ID: {a.id} | Danışan: {a.client.name}")
            print(f"   Durum: {a.analysis_status.upper()} | İlerleme: {a.analysis_progress}%")
            print(f"   Tarih Aralığı: {a.date_range}")
            print(f"   Oturum Sayısı: {a.sessions_analyzed}")
            print(f"   Rapor: {'Mevcut (' + str(len(a.analysis_text)) + ' karakter)' if a.analysis_text else 'Yok'}")
            print(f"   Task ID: {a.task_id or 'Yok'}")
            print(f"   Oluşturulma: {a.created_at}")
            print()

def check_celery_ready():
    """Celery ve Redis kontrolü"""
    import subprocess
    
    print(f"\n{'='*80}")
    print("🔍 SİSTEM KONTROLÜ")
    print(f"{'='*80}\n")
    
    # Redis kontrolü
    try:
        result = subprocess.run(['redis-cli', 'ping'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and 'PONG' in result.stdout:
            print("✅ Redis çalışıyor")
        else:
            print("❌ Redis çalışmıyor!")
    except Exception as e:
        print(f"❌ Redis kontrolü başarısız: {e}")
    
    # Celery worker kontrolü
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        celery_count = result.stdout.count('celery worker')
        if celery_count > 0:
            print(f"✅ Celery worker çalışıyor ({celery_count} process)")
        else:
            print("❌ Celery worker çalışmıyor!")
    except Exception as e:
        print(f"❌ Celery kontrolü başarısız: {e}")
    
    print()

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--check':
        check_celery_ready()
    
    show_progress_analyses()
    
    print(f"{'='*80}")
    print("💡 İPUCU:")
    print("   - Sistem kontrolü için: python test_progress_analysis.py --check")
    print("   - Yeni analiz oluşturmak için: Web arayüzünü kullanın")
    print(f"{'='*80}\n")

