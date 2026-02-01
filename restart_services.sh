cd /home/sefa4/projectPDR
source venv/bin/activate

echo ""
echo "1. Eski processleri durduruluyor..."

# Celery worker'ı durdur
pkill -f "celery.*worker" && echo "   ✅ Celery worker durduruldu" || echo "   ⚠️  Celery worker zaten durmuş"

# Flask'ı durdur
pkill -f "python3 run.py" && echo "   ✅ Flask durduruldu" || echo "   ⚠️  Flask zaten durmuş"

# 2 saniye bekle
sleep 2

echo ""
echo "2. Redis kontrol ediliyor..."
redis-cli -p 6380 ping > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "   ✅ Redis çalışıyor"
else
    echo "   ⚠️  Redis başlatılıyor..."
    redis-server --port 6380 --daemonize yes
    sleep 1
    echo "   ✅ Redis başlatıldı"
fi

echo ""
echo "3. Celery worker başlatılıyor..."
nohup celery -A app.celery_config.celery worker --loglevel=info -E > logs/celery.log 2>&1 &
sleep 2
echo "   ✅ Celery worker başlatıldı (PID: $!)"

echo ""
echo "4. Flask uygulaması başlatılıyor..."
nohup python3 run.py > logs/flask.log 2>&1 &
sleep 2
echo "   ✅ Flask başlatıldı (PID: $!)"

echo ""
echo "=================================================="
echo "✅ TÜM SERVİSLER BAŞARIYLA BAŞLATILDI!"
echo "=================================================="

echo ""
echo "📊 Çalışan Processler:"
ps aux | grep -E "celery|python3 run.py|redis-server" | grep -v grep

echo ""
echo "📝 Logları izlemek için:"
echo "   Celery: tail -f logs/celery.log"
echo "   Flask:  tail -f logs/flask.log"

echo ""
echo "🌐 Web sitesi: http://127.0.0.1:8000"
echo ""

