#!/bin/bash
# Tüm servisleri temizle ve yeniden başlat

echo "🔄 Tüm servisleri yeniden başlatıyorum..."

# 1. Tüm servisleri durdur
echo "1️⃣ Servisleri durduruyorum..."
sudo systemctl stop gunicorn celery-worker pdr-app 2>/dev/null
pkill -9 -f gunicorn
pkill -9 -f celery
sleep 3

# 2. Gunicorn'u başlat
echo "2️⃣ Gunicorn başlatılıyor..."
cd /home/sefa4/projectPDR
source venv/bin/activate
nohup gunicorn --workers 2 --bind 0.0.0.0:8000 --timeout 600 run:app > logs/gunicorn.log 2>&1 &
sleep 3

# 3. Celery'yi başlat
echo "3️⃣ Celery başlatılıyor..."
nohup celery -A app.celery_config.celery worker --loglevel=info --concurrency=2 -n pdr_worker@%h > logs/celery_worker.log 2>&1 &
sleep 5

# 4. Durumu kontrol et
echo ""
echo "📊 Servis Durumu:"
echo "════════════════════════════════════════"

GUNICORN_COUNT=$(ps aux | grep "gunicorn.*run:app" | grep -v grep | wc -l)
echo "Gunicorn: $GUNICORN_COUNT process"

CELERY_COUNT=$(ps aux | grep "celery.*worker" | grep -v grep | wc -l)
echo "Celery: $CELERY_COUNT process"

REDIS_STATUS=$(redis-cli ping 2>/dev/null)
echo "Redis: $REDIS_STATUS"

echo "════════════════════════════════════════"
echo ""
echo "✅ Servisler yeniden başlatıldı!"
echo ""
echo "🧪 Test etmek için:"
echo "   1. Web arayüzünde yeni ilerleyiş analizi oluşturun"
echo "   2. ./check_analysis.sh komutunu çalıştırın"
echo ""

