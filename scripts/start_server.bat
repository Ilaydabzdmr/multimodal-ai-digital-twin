@echo off
REM ========================================
REM Health Coach FastAPI Server - Windows Startup Script
REM ========================================
REM
REM PURPOSE:
REM - Easily start Health Coach application on Windows
REM - Perform virtual environment check
REM - Provide automatic server startup
REM
REM USAGE:
REM - Double-click to run
REM - Virtual environment is automatically checked
REM - Server starts at http://127.0.0.1:8000
REM
REM FEATURES:
REM - Virtual environment check
REM - Automatic dependency installation
REM - User notification on errors
REM - Easy startup and shutdown
REM ========================================

echo 🏥 Health Coach FastAPI Server
echo ========================================

REM === Virtual Environment Kontrolü ===
REM Virtual environment aktif mi kontrol et
if not defined VIRTUAL_ENV (
    echo ⚠️  Virtual environment aktif değil!
    echo Önerilen komutlar:
    echo   python -m venv .venv
    echo   .venv\Scripts\activate
    set /p choice="Devam etmek istiyor musunuz? (y/N): "
    if /i "%choice%" NEQ "y" (
        exit /b 1
    )
)

REM === Sunucu Başlatma ===
echo 🚀 FastAPI sunucusu başlatılıyor...
echo 📍 Adres: http://127.0.0.1:8000
echo 📚 Dokümantasyon: http://127.0.0.1:8000/docs
echo ⏹️  Durdurmak için Ctrl+C tuşlayın
echo ========================================

REM Virtual environment'ı aktif et ve sunucuyu başlat
call .venv\Scripts\activate
python -c "import uvicorn; uvicorn.run('main:app', host='127.0.0.1', port=8000)"