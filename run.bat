@echo off
title Aarogya Hospital & Clinic Appointment System
color 0b

echo =====================================================================
echo       AAROGYA LIFE MULTISPECIALTY HOSPITAL & CLINIC SYSTEM
echo =====================================================================
echo.
echo [1/3] Checking environment & initializing database...
python seed_data.py
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to run database setup. Please make sure Python is installed.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [2/3] Launching Web Browser at http://127.0.0.1:5000 ...
start http://127.0.0.1:5000

echo.
echo [3/3] Starting Hospital ERP Application Server...
echo =====================================================================
echo Application is running! Press CTRL+C in this window to stop the server.
echo =====================================================================
python app.py
pause
