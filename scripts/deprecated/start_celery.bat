@echo off
REM Celery Worker Başlatma Scripti (Windows)
REM Bu script Celery worker'ı başlatır

echo ========================================
echo PDR Analiz Sistemi - Celery Worker
echo ========================================
echo.

REM Python sanal ortamını aktifleştir (eğer varsa)
if exist venv\Scripts\activate.bat (
    echo Virtual environment aktifleştiriliyor...
    call venv\Scripts\activate.bat
)

REM Redis çalışıyor olduğunu varsay (port 6380)
echo Redis port 6380'de çalışıyor olmalı...
echo.

REM Celery worker'ı başlat
echo Celery worker başlatılıyor...
echo ----------------------------------------
echo Çalışma dizini: %CD%
echo Python: 
python --version
echo ----------------------------------------
echo.

REM Celery worker'ı log level INFO ile başlat
celery -A app.celery_config.celery worker --loglevel=info --pool=solo -E

REM Hata durumunda
if errorlevel 1 (
    echo.
    echo [HATA] Celery worker başlatılamadı!
    pause
)

