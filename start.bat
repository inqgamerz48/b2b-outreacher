@echo off
echo ==========================================
echo 🚀 B2B Outreach Pro - One Click Launch
echo ==========================================

echo [1/3] Checking Python...
python --version
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    pause
    exit
)

echo [2/3] Installing Dependencies...
pip install -r requirements.txt
pip install aiohttp

echo [3/3] Starting Server...
echo Visit http://localhost:8000 in your browser.
python server.py

pause
