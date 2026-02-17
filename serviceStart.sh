#!/bin/bash
# PDR Video Analiz Sistemi - Servis Başlatma Scripti
# Tüm servisleri (Redis, Celery, Flask) başlatır

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║       PDR VİDEO ANALİZ SİSTEMİ - SERVİS BAŞLATMA           ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Proje dizinine git
cd /var/www/projectPDR

# Sanal ortamı aktif et
source venv/bin/activate

# Renkli çıktı için
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1️⃣  REDIS SERVER BAŞLATILIYOR"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Redis durumunu kontrol et
redis-cli -p 6380 ping > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo -e "${YELLOW}⚠️  Redis zaten çalışıyor (port 6380)${NC}"
else
    echo "   Redis başlatılıyor..."
    redis-server --port 6380 --daemonize yes
    sleep 2
    
    # Başarı kontrolü
    redis-cli -p 6380 ping > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Redis başarıyla başlatıldı (port 6380)${NC}"
    else
        echo -e "${RED}❌ Redis başlatılamadı!${NC}"
        exit 1
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2️⃣  CELERY WORKER BAŞLATILIYOR"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Eski Celery worker'ları kontrol et
CELERY_COUNT=$(ps aux | grep "celery.*worker" | grep -v grep | wc -l)
if [ $CELERY_COUNT -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Celery zaten çalışıyor ($CELERY_COUNT process)${NC}"
else
    echo "   Celery worker başlatılıyor..."
    celery -A app.celery_config.celery worker --loglevel=info -E --detach --logfile=logs/celery_worker.log
    sleep 3
    
    # Başarı kontrolü
    CELERY_COUNT=$(ps aux | grep "celery.*worker" | grep -v grep | wc -l)
    if [ $CELERY_COUNT -gt 0 ]; then
        echo -e "${GREEN}✅ Celery worker başarıyla başlatıldı ($CELERY_COUNT process)${NC}"
        echo "   Log: logs/celery_worker.log"
    else
        echo -e "${RED}❌ Celery worker başlatılamadı!${NC}"
        exit 1
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3️⃣  FLASK UYGULAMASI BAŞLATILIYOR"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Eski Flask process'ini kontrol et
FLASK_PID=$(ps aux | grep "python3 run.py" | grep -v grep | awk '{print $2}')
if [ ! -z "$FLASK_PID" ]; then
    echo -e "${YELLOW}⚠️  Flask zaten çalışıyor (PID: $FLASK_PID)${NC}"
else
    echo "   Flask uygulaması başlatılıyor..."
    nohup python3 run.py > logs/flask_app.log 2>&1 &
    FLASK_PID=$!
    sleep 3
    
    # Başarı kontrolü
    if ps -p $FLASK_PID > /dev/null; then
        echo -e "${GREEN}✅ Flask uygulaması başarıyla başlatıldı (PID: $FLASK_PID)${NC}"
        echo "   Port: 8000"
        echo "   Log: logs/flask_app.log"
    else
        echo -e "${RED}❌ Flask uygulaması başlatılamadı!${NC}"
        echo "   Log dosyasını kontrol edin: tail -20 logs/flask_app.log"
        exit 1
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ TÜM SERVİSLER BAŞARIYLA BAŞLATILDI"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 ÇALIŞAN SERVİSLER:"
echo ""

# Redis durumu
echo -n "   🔴 Redis (port 6380): "
redis-cli -p 6380 ping > /dev/null 2>&1 && echo -e "${GREEN}ÇALIŞIYOR${NC}" || echo -e "${RED}DURMUŞ${NC}"

# Celery durumu
CELERY_COUNT=$(ps aux | grep "celery.*worker" | grep -v grep | wc -l)
echo -ne "   🔴 Celery Worker: "
if [ $CELERY_COUNT -gt 0 ]; then
    echo -e "${GREEN}ÇALIŞIYOR ($CELERY_COUNT process)${NC}"
else
    echo -e "${RED}DURMUŞ${NC}"
fi

# Flask durumu
FLASK_PID=$(ps aux | grep "python3 run.py" | grep -v grep | awk '{print $2}')
echo -ne "   🔴 Flask (port 8000): "
if [ ! -z "$FLASK_PID" ]; then
    echo -e "${GREEN}ÇALIŞIYOR (PID: $FLASK_PID)${NC}"
else
    echo -e "${RED}DURMUŞ${NC}"
fi

echo ""
echo "🌐 WEB ADRESİ:"
echo "   http://$(hostname -I | awk '{print $1}'):8000"
echo "   http://localhost:8000"
echo ""
echo "📝 LOGLARI İZLEMEK İÇİN:"
echo "   Celery:  tail -f logs/celery_worker.log"
echo "   Flask:   tail -f logs/flask_app.log"
echo ""
echo "🛑 SERVİSLERİ DURDURMAK İÇİN:"
echo "   ./serviceStop.sh"
echo ""

