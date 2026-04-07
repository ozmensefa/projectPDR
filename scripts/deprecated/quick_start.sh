#!/bin/bash
# YAKADES - Hızlı Başlangıç Scripti

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                YAKADES                                         ║"
echo "║            İlerleyiş Analizi - Hızlı Başlangıç                 ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo

# Renk kodları
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 1. Redis Kontrolü
echo -e "${BLUE}[1/5]${NC} Redis servisini kontrol ediliyor..."
if redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Redis çalışıyor"
else
    echo -e "${RED}✗${NC} Redis çalışmıyor!"
    echo -e "${YELLOW}→${NC} Redis'i başlatmak için: ${BLUE}sudo systemctl start redis${NC}"
    echo -e "${YELLOW}→${NC} veya: ${BLUE}redis-server${NC}"
    exit 1
fi

# 2. Python Virtual Environment
echo -e "${BLUE}[2/5]${NC} Python sanal ortamı kontrol ediliyor..."
if [ -f venv/bin/activate ]; then
    source venv/bin/activate
    echo -e "${GREEN}✓${NC} Virtual environment aktifleştirildi"
else
    echo -e "${YELLOW}⚠${NC} Virtual environment bulunamadı"
    echo -e "${YELLOW}→${NC} Devam ediliyor..."
fi

# 3. Gerekli Paketler
echo -e "${BLUE}[3/5]${NC} Gerekli Python paketleri kontrol ediliyor..."
if python -c "import redis, celery, flask" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Gerekli paketler yüklü"
else
    echo -e "${RED}✗${NC} Bazı paketler eksik!"
    echo -e "${YELLOW}→${NC} Yüklemek için: ${BLUE}pip install -r requirements.txt${NC}"
    exit 1
fi

# 4. Test Scripti
echo -e "${BLUE}[4/5]${NC} Sistem kontrolü yapılıyor..."
python test_celery_setup.py > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Sistem kontrolü başarılı"
else
    echo -e "${YELLOW}⚠${NC} Bazı kontroller başarısız (detaylar için: python test_celery_setup.py)"
fi

# 5. Celery Worker Kontrolü
echo -e "${BLUE}[5/5]${NC} Celery worker kontrolü..."
if pgrep -f "celery.*worker" > /dev/null; then
    echo -e "${GREEN}✓${NC} Celery worker zaten çalışıyor"
    echo -e "${YELLOW}→${NC} Worker PID: $(pgrep -f "celery.*worker" | head -1)"
else
    echo -e "${YELLOW}⚠${NC} Celery worker çalışmıyor"
    echo
    echo -e "${BLUE}Celery worker'ı başlatmak ister misiniz? (y/n)${NC}"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        echo -e "${GREEN}✓${NC} Celery worker başlatılıyor..."
        echo -e "${YELLOW}→${NC} Worker'ı durdurmak için: ${BLUE}Ctrl+C${NC}"
        echo
        sleep 2
        celery -A celery_worker.celery worker --loglevel=info --pool=solo
    else
        echo -e "${YELLOW}→${NC} Manuel başlatmak için: ${BLUE}./start_celery.sh${NC}"
    fi
fi

echo
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                    SİSTEM HAZIR!                               ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo
echo -e "${GREEN}Sistem başarıyla hazırlandı!${NC}"
echo
echo -e "${BLUE}Sıradaki Adımlar:${NC}"
echo -e "  1. Flask uygulamasını başlatın: ${GREEN}python run.py${NC}"
echo -e "  2. Tarayıcıda açın: ${GREEN}http://localhost:5000${NC}"
echo -e "  3. Bir danışan seçin ve 'İlerleyiş Analizi' butonuna tıklayın"
echo
echo -e "${BLUE}Yararlı Komutlar:${NC}"
echo -e "  • Sistem kontrolü: ${GREEN}python test_celery_setup.py${NC}"
echo -e "  • Debug: ${GREEN}python debug_progress_analysis.py${NC}"
echo -e "  • Celery worker: ${GREEN}./start_celery.sh${NC}"
echo -e "  • Monitoring: ${GREEN}celery -A celery_worker.celery flower --port=5555${NC}"
echo

