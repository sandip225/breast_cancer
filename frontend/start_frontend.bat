@echo off
REM Start Frontend Server

echo.
echo ========================================
echo Starting Frontend Server
echo ========================================
echo.

cd /d "%~dp0"

echo Starting React development server...
echo Frontend will be available at: http://localhost:3000
echo.
echo Press Ctrl+C to stop the server
echo.

npm start

