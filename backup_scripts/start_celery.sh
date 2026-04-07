#!/bin/bash
# Celery Worker Başlatma Scripti (Linux/Mac)
# Bu script Celery worker'ı başlatır

echo "========================================"
echo "YAKADES - Celery Worker"
echo "========================================"
echo

# Python sanal ortamını aktifleştir (eğer varsa)
if [ -f venv/bin/activate ]; then
    echo "Virtual environment aktifleştiriliyor..."
    source venv/bin/activate
fi

# Redis çalışıyor mu kontrol et
echo "Redis kontrolü yapılıyor..."
if ! redis-cli ping > /dev/null 2>&1; then
    echo "[HATA] Redis çalışmıyor! Lütfen önce Redis'i başlatın."
    echo
    echo "Redis kurulumu için:"
    echo "  Ubuntu/Debian: sudo apt-get install redis-server"
    echo "  macOS: brew install redis"
    echo "  CentOS/RHEL: sudo yum install redis"
    echo
    echo "Redis başlatma:"
    echo "  sudo systemctl start redis"
    echo "  veya"
    echo "  redis-server"
    echo
    exit 1
fi

echo "[OK] Redis çalışıyor."
echo

# Celery worker'ı başlat
echo "Celery worker başlatılıyor..."
echo "----------------------------------------"
echo "Çalışma dizini: $(pwd)"
echo "Python: $(python --version)"
echo "----------------------------------------"
echo

# Celery worker'ı log level INFO ile başlat
celery -A app.celery_config.celery worker --loglevel=info -E

# Hata durumunda
if [ $? -ne 0 ]; then
    echo
    echo "[HATA] Celery worker başlatılamadı!"
    exit 1
fi

