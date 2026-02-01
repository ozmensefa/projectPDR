#!/bin/bash
cd /home/sefa4/projectPDR
source venv/bin/activate

python3 << 'EOF'
from app import create_app
from app.models import ProgressAnalysis
from datetime import datetime, timedelta

app = create_app()
with app.app_context():
    # Son 5 dakikada oluşturulan analizleri bul
    five_min_ago = datetime.utcnow() - timedelta(minutes=5)
    recent = ProgressAnalysis.query.filter(
        ProgressAnalysis.created_at >= five_min_ago
    ).order_by(ProgressAnalysis.created_at.desc()).all()
    
    if recent:
        print(f'\n📊 Son 5 dakikada {len(recent)} analiz:')
        for a in recent:
            print(f'\n  ID: {a.id}')
            print(f'  Status: {a.analysis_status}')
            print(f'  Progress: {a.analysis_progress}%')
            print(f'  Task ID: {a.task_id or "YOK - SORUN!"}')
            print(f'  Oluşturulma: {a.created_at}')
    else:
        print('\n❌ Son 5 dakikada analiz bulunamadı')
        print('Lütfen yeni bir ilerleyiş analizi oluşturun\n')
EOF

