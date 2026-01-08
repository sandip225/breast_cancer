@echo off
REM Breast Cancer Detection Project Startup Script

echo.
echo ========================================
echo Breast Cancer Detection System
echo ========================================
echo.
echo Starting Backend and Frontend...
echo.

REM Start Backend in new window
echo [1/2] Starting Backend Server (FastAPI)...
start "Backend - FastAPI" cmd /k "cd backend && .\venv\Scripts\activate && python -m uvicorn main:app --reload --host 127.0.0.1 --port 8001"

REM Wait a bit for backend to start
timeout /t 5 /nobreak >nul

REM Start Frontend in new window
echo [2/2] Starting Frontend Server (React)...
start "Frontend - React" cmd /k "cd frontend && npm start"

echo.
echo ========================================
echo Servers Starting...
echo ========================================
echo.
echo Backend:  http://localhost:8001
echo Frontend: http://localhost:3001
echo API Docs: http://localhost:8001/docs
echo.
echo Both servers will open in separate windows.
echo Close those windows to stop the servers.
echo.
echo Press any key to exit this window...
pause >nul

