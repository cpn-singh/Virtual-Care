@echo off
title Virtual Care Backend & Tunnel Runner
echo ========================================================
echo   Virtual Care Telemedicine - Backend & Tunnel
echo ========================================================
echo.
echo [1/2] Launching Django Backend on port 8000...
start "Virtual Care Django Server" cmd /k "backend\venv\Scripts\python.exe backend\manage.py runserver 0.0.0.0:8000"

echo [2/2] Launching Ngrok Static Tunnel (interlobate-isidro-palmately)...
start "Virtual Care Static Tunnel" cmd /k "ngrok http 8000"

echo.
echo ========================================================
echo   All services are running!
echo   Permanent API URL: https://interlobate-isidro-palmately.ngrok-free.dev/api/v1
echo ========================================================
pause
