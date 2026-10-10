@echo off
title Sentinel - Privileged Access Monitoring Tool
echo ========================================================
echo   SENTINEL - Privileged Access Monitoring Tool (T2-PS4)
echo ========================================================
echo.
echo Starting Sentinel FastAPI Backend and Production SPA...

cd /d "%~dp0backend"

:: Start Uvicorn in a separate persistent window
start "Sentinel Backend & Web Server" "C:\Users\kavin raja m\AppData\Local\Programs\Python\Python312\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 8000

echo Waiting for server to initialize on http://localhost:8000 ...
timeout /t 3 /nobreak >nul

:: Open browser
start "" "http://localhost:8000"

echo.
echo Sentinel is active and open in your browser!
echo Web Application: http://localhost:8000
echo API Docs:        http://localhost:8000/docs
echo.
echo (Keep this terminal or the server window open while using Sentinel)
pause
