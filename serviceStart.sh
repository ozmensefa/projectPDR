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
echo "3️⃣  GUNICORN UYGULAMA SUNUCUSU BAŞLATILIYOR"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Gunicorn veya Flask process'ini kontrol et
APP_PIDS=$(pgrep -f 'gunicorn.*app:create_app' 2>/dev/null)
if [ ! -z "$APP_PIDS" ]; then
    APP_COUNT=$(echo $APP_PIDS | wc -w)
    echo -e "${YELLOW}⚠️  Gunicorn zaten çalışıyor ($APP_COUNT process)${NC}"
else
    echo "   Gunicorn başlatılıyor (4 worker, port 8000)..."
    nohup python3 -m gunicorn -w 4 -b 127.0.0.1:8000 --timeout 600 "app:create_app()" > logs/gunicorn.log 2>&1 &
    GUNICORN_PID=$!
    sleep 3
    
    # Başarı kontrolü
    APP_PIDS=$(pgrep -f 'gunicorn.*app:create_app' 2>/dev/null)
    if [ ! -z "$APP_PIDS" ]; then
        APP_COUNT=$(echo $APP_PIDS | wc -w)
        echo -e "${GREEN}✅ Gunicorn başarıyla başlatıldı ($APP_COUNT process, PID: $GUNICORN_PID)${NC}"
        echo "   Port: 8000"
        echo "   Log: logs/gunicorn.log"
    else
        echo -e "${RED}❌ Gunicorn başlatılamadı!${NC}"
        echo "   Log dosyasını kontrol edin: tail -20 logs/gunicorn.log"
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

# Uygulama sunucusu durumu
APP_PIDS=$(pgrep -f 'gunicorn.*app:create_app' 2>/dev/null)
echo -ne "   🟢 Gunicorn (port 8000): "
if [ ! -z "$APP_PIDS" ]; then
    APP_COUNT=$(echo $APP_PIDS | wc -w)
    echo -e "${GREEN}ÇALIŞIYOR ($APP_COUNT process)${NC}"
else
    echo -e "${RED}DURMUŞ${NC}"
fi

echo ""
echo "🌐 WEB ADRESİ:"
echo "   https://yakades.com.tr"
echo "   http://127.0.0.1:8000 (yerel)"
echo ""
echo "📝 LOGLARI İZLEMEK İÇİN:"
echo "   Celery:   tail -f logs/celery_worker.log"
echo "   Gunicorn: tail -f logs/gunicorn.log"
echo ""
echo "🛑 SERVİSLERİ DURDURMAK İÇİN:"
echo "   ./serviceStop.sh"
echo ""

