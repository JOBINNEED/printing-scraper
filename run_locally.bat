@echo off
echo ========================================
echo   MarketIntel - Local Runner
echo ========================================
echo.
echo NOTE: This script assumes you have MongoDB installed and running.
echo If you haven't started MongoDB, the backend will fail to connect.
echo.
echo Starting services...
echo.

echo [1/2] Starting Backend API...
start "MarketIntel Backend" cmd /k "cd backend && python -m uvicorn server:app --host 0.0.0.0 --port 8001 --reload"

echo [2/2] Starting Frontend...
start "MarketIntel Frontend" cmd /k "cd frontend && npm start"

echo.
echo Services launched in separate windows.
echo Dashboard should open at: http://localhost:3000
echo API running at: http://localhost:8001
echo.
pause
