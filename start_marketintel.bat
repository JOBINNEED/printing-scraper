@echo off
echo ========================================
echo   MarketIntel - Machinery Tracker
echo ========================================
echo.
echo Starting services...
echo.

cd /app

echo [1/3] Starting MongoDB...
start /B mongod --dbpath /data/db

echo [2/3] Starting Backend API...
cd /app/backend
start /B python -m uvicorn server:app --host 0.0.0.0 --port 8001

echo [3/3] Starting Frontend...
cd /app/frontend
start /B yarn start

echo.
echo ========================================
echo   MarketIntel is starting...
echo ========================================
echo.
echo Dashboard will open at: http://localhost:3000
echo API running at: http://localhost:8001
echo.
echo Press Ctrl+C to stop all services
echo.

timeout /t 5
start http://localhost:3000

pause
