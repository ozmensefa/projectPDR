#!/bin/bash
#############################################################################
# İlerleyiş Analizi Düzeltmesi - Servis Yeniden Başlatma
# Tarih: 2025-11-07
#############################################################################

echo "════════════════════════════════════════════════════════════"
echo "🔄 SERVİSLERİ YENİDEN BAŞLATMA"
echo "════════════════════════════════════════════════════════════"
echo ""

# Renk kodları
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 1. Tüm servisleri durdur
echo -e "${YELLOW}1️⃣ Servisleri durduruyorum...${NC}"
pkill -9 -f gunicorn 2>/dev/null
pkill -9 -f celery 2>/dev/null
sleep 3
echo -e "${GREEN}   ✅ Servisler durduruldu${NC}"
echo ""

# 2. Çalışma dizinine git
cd /home/sefa4/projectPDR
source venv/bin/activate

# 3. Gunicorn'u başlat
echo -e "${YELLOW}2️⃣ Gunicorn başlatılıyor...${NC}"
nohup gunicorn --workers 2 --bind 0.0.0.0:8000 --timeout 600 run:app > logs/gunicorn.log 2>&1 &
sleep 3

GUNICORN_COUNT=$(ps aux | grep "gunicorn.*run:app" | grep -v grep | wc -l)
if [ "$GUNICORN_COUNT" -ge 3 ]; then
    echo -e "${GREEN}   ✅ Gunicorn başlatıldı ($GUNICORN_COUNT process)${NC}"
else
    echo -e "${RED}   ❌ Gunicorn başlatılamadı!${NC}"
fi
echo ""

# 4. Celery'yi başlat
echo -e "${YELLOW}3️⃣ Celery başlatılıyor...${NC}"
nohup celery -A app.celery_config.celery worker --loglevel=info --concurrency=2 > logs/celery.log 2>&1 &
sleep 5

CELERY_COUNT=$(ps aux | grep "celery.*worker" | grep -v grep | wc -l)
if [ "$CELERY_COUNT" -ge 3 ]; then
    echo -e "${GREEN}   ✅ Celery başlatıldı ($CELERY_COUNT process)${NC}"
else
    echo -e "${RED}   ❌ Celery başlatılamadı!${NC}"
fi
echo ""

# 5. Redis kontrolü
echo -e "${YELLOW}4️⃣ Redis kontrol ediliyor...${NC}"
REDIS_STATUS=$(redis-cli ping 2>/dev/null)
if [ "$REDIS_STATUS" = "PONG" ]; then
    echo -e "${GREEN}   ✅ Redis çalışıyor${NC}"
else
    echo -e "${RED}   ❌ Redis çalışmıyor!${NC}"
fi
echo ""

# 6. Task kontrolü
echo -e "${YELLOW}5️⃣ Celery task'ları kontrol ediliyor...${NC}"
sleep 2
celery -A app.celery_config.celery inspect registered 2>&1 | grep -q "analyze_progress"
if [ $? -eq 0 ]; then
    echo -e "${GREEN}   ✅ analyze_progress task kayıtlı${NC}"
else
    echo -e "${RED}   ❌ analyze_progress task bulunamadı!${NC}"
fi

celery -A app.celery_config.celery inspect registered 2>&1 | grep -q "analyze_video"
if [ $? -eq 0 ]; then
    echo -e "${GREEN}   ✅ analyze_video task kayıtlı${NC}"
else
    echo -e "${RED}   ❌ analyze_video task bulunamadı!${NC}"
fi
echo ""

# 7. Özet
echo "════════════════════════════════════════════════════════════"
echo -e "${GREEN}✅ SERVİSLER YENİDEN BAŞLATILDI!${NC}"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "📊 Durum Özeti:"
echo "   • Gunicorn: $GUNICORN_COUNT process"
echo "   • Celery: $CELERY_COUNT process"
echo "   • Redis: $REDIS_STATUS"
echo ""
echo "🧪 Test için:"
echo "   1. Web arayüzünde yeni ilerleyiş analizi oluştur"
echo "   2. ./check_analysis.sh komutunu çalıştır"
echo "   3. Task ID'nin dolu olduğunu kontrol et"
echo ""
echo "📋 Log dosyaları:"
echo "   • Gunicorn: tail -f logs/gunicorn.log"
echo "   • Celery: tail -f logs/celery.log"
echo ""

