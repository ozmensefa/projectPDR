#!/bin/bash
# PDR Video Analiz Sistemi - Servis Durdurma Scripti
# Tüm servisleri (Flask, Celery, Redis) güvenli şekilde durdurur

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║       PDR VİDEO ANALİZ SİSTEMİ - SERVİS DURDURMA           ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Renkli çıktı için
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1️⃣  FLASK UYGULAMASI DURDURULUYOR"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

FLASK_PIDS=$(ps aux | grep "python3 run.py" | grep -v grep | awk '{print $2}')
if [ -z "$FLASK_PIDS" ]; then
    echo -e "${YELLOW}⚠️  Flask zaten durmuş${NC}"
else
    echo "   Flask process'leri durduruluyor..."
    for PID in $FLASK_PIDS; do
        kill $PID 2>/dev/null && echo "   - PID $PID durduruldu"
    done
    sleep 2
    
    # Force kill gerekiyorsa
    FLASK_PIDS=$(ps aux | grep "python3 run.py" | grep -v grep | awk '{print $2}')
    if [ ! -z "$FLASK_PIDS" ]; then
        echo "   Zorla durduruluyor (SIGKILL)..."
        for PID in $FLASK_PIDS; do
            kill -9 $PID 2>/dev/null
        done
        sleep 1
    fi
    
    # Kontrol
    FLASK_PIDS=$(ps aux | grep "python3 run.py" | grep -v grep | awk '{print $2}')
    if [ -z "$FLASK_PIDS" ]; then
        echo -e "${GREEN}✅ Flask başarıyla durduruldu${NC}"
    else
        echo -e "${RED}❌ Flask durdurulamadı!${NC}"
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2️⃣  CELERY WORKER DURDURULUYOR"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

CELERY_COUNT=$(ps aux | grep "celery.*worker" | grep -v grep | wc -l)
if [ $CELERY_COUNT -eq 0 ]; then
    echo -e "${YELLOW}⚠️  Celery zaten durmuş${NC}"
else
    echo "   Celery worker process'leri durduruluyor ($CELERY_COUNT process)..."
    
    # Önce graceful shutdown dene
    pkill -TERM -f "celery.*worker" 2>/dev/null
    sleep 3
    
    # Hala çalışıyorsa force kill
    CELERY_COUNT=$(ps aux | grep "celery.*worker" | grep -v grep | wc -l)
    if [ $CELERY_COUNT -gt 0 ]; then
        echo "   Zorla durduruluyor (SIGKILL)..."
        pkill -9 -f "celery.*worker" 2>/dev/null
        sleep 2
    fi
    
    # Kontrol
    CELERY_COUNT=$(ps aux | grep "celery.*worker" | grep -v grep | wc -l)
    if [ $CELERY_COUNT -eq 0 ]; then
        echo -e "${GREEN}✅ Celery worker başarıyla durduruldu${NC}"
    else
        echo -e "${RED}❌ Celery worker tamamen durdurulamadı ($CELERY_COUNT process kaldı)${NC}"
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3️⃣  REDIS SERVER DURDURULUYOR"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

redis-cli -p 6380 ping > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}⚠️  Redis zaten durmuş${NC}"
else
    echo "   Redis server durduruluyor..."
    redis-cli -p 6380 shutdown 2>/dev/null
    sleep 2
    
    # Kontrol
    redis-cli -p 6380 ping > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        echo -e "${GREEN}✅ Redis başarıyla durduruldu${NC}"
    else
        echo -e "${RED}❌ Redis durdurulamadı!${NC}"
        echo "   Manuel durdurma: redis-cli -p 6380 shutdown"
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ TÜM SERVİSLER DURDURULDU"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 DURUM KONTROLÜ:"
echo ""

# Redis durumu
echo -n "   🔴 Redis (port 6380): "
redis-cli -p 6380 ping > /dev/null 2>&1 && echo -e "${RED}ÇALIŞIYOR${NC}" || echo -e "${GREEN}DURMUŞ${NC}"

# Celery durumu
CELERY_COUNT=$(ps aux | grep "celery.*worker" | grep -v grep | wc -l)
echo -ne "   🔴 Celery Worker: "
if [ $CELERY_COUNT -eq 0 ]; then
    echo -e "${GREEN}DURMUŞ${NC}"
else
    echo -e "${RED}ÇALIŞIYOR ($CELERY_COUNT process)${NC}"
fi

# Flask durumu
FLASK_PID=$(ps aux | grep "python3 run.py" | grep -v grep | awk '{print $2}')
echo -ne "   🔴 Flask (port 8000): "
if [ -z "$FLASK_PID" ]; then
    echo -e "${GREEN}DURMUŞ${NC}"
else
    echo -e "${RED}ÇALIŞIYOR (PID: $FLASK_PID)${NC}"
fi

echo ""
echo "🚀 SERVİSLERİ TEKRAR BAŞLATMAK İÇİN:"
echo "   ./serviceStart.sh"
echo ""

