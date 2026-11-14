@echo off
title Virtual Care - Full Stack Startup
echo ========================================================
echo   Starting Virtual Care - Full Stack Telehealth Platform
echo ========================================================
echo.

set "ROOT_DIR=%~dp0"

echo [1/2] Launching Django Backend Server on port 8000...
start "Virtual Care - Backend (Django)" cmd /k "cd /d %ROOT_DIR%backend && (if not exist venv python -m venv venv) && call venv\Scripts\activate && pip install -r requirements.txt && python manage.py migrate && python manage.py seed_demo_data && python manage.py runserver 0.0.0.0:8000"

echo [2/2] Launching React Vite Frontend on port 5173...
start "Virtual Care - Frontend (React + Vite)" cmd /k "cd /d %ROOT_DIR%frontend && npm run dev"

echo.
echo ========================================================
echo   Servers are starting in separate terminal windows:
echo   - Backend:  http://127.0.0.1:8000/
echo   - Frontend: http://localhost:5173/
echo ========================================================
echo.
timeout /t 5
