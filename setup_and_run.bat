@echo off
REM Setup and run the Breast Cancer Detection System

echo.
echo ========================================
echo Breast Cancer Detection System Setup
echo ========================================
echo.

REM Check if model file exists
echo [1/5] Checking model file...
if exist "backend\models\breast_cancer_model.keras" (
    for /F "tokens=*" %%A in ('powershell -Command "'{0:N0}' -f (Get-Item 'backend\models\breast_cancer_model.keras').Length / 1MB"') do set SIZE=%%A
    echo ✓ Model found: backend\models\breast_cancer_model.keras (!SIZE! MB)
) else (
    echo ✗ ERROR: Model file not found at backend\models\breast_cancer_model.keras
    echo Please ensure the model file is in the correct location.
    pause
    exit /b 1
)

echo.
echo [2/5] Stopping existing containers...
docker-compose down >nul 2>&1
echo ✓ Done

echo.
echo [3/5] Building Docker images (this may take a few minutes)...
docker-compose build --no-cache
if errorlevel 1 (
    echo ✗ Build failed
    pause
    exit /b 1
)
echo ✓ Build complete

echo.
echo [4/5] Starting services...
docker-compose up -d
echo ✓ Services starting...

echo.
echo [5/5] Waiting for backend to initialize (60 seconds)...
timeout /t 60 /nobreak

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Frontend: http://localhost:3001
echo Backend:  http://localhost:8001
echo Health:   http://localhost:8001/health
echo.
echo Logs:     docker-compose logs -f
echo Stop:     docker-compose down
echo.
pause
