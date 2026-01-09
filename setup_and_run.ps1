# Setup and run the Breast Cancer Detection System

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Breast Cancer Detection System Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if model file exists
Write-Host "[1/5] Checking model file..." -ForegroundColor Yellow
$modelPath = "backend\models\breast_cancer_model.keras"
if (Test-Path $modelPath) {
    $size = (Get-Item $modelPath).Length / 1MB
    Write-Host "✓ Model found: $modelPath ($([math]::Round($size, 1)) MB)" -ForegroundColor Green
} else {
    Write-Host "✗ ERROR: Model file not found at $modelPath" -ForegroundColor Red
    Write-Host "Please ensure the model file is in the correct location." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "[2/5] Stopping existing containers..." -ForegroundColor Yellow
docker-compose down 2>$null
Write-Host "✓ Done" -ForegroundColor Green

Write-Host ""
Write-Host "[3/5] Building Docker images (this may take a few minutes)..." -ForegroundColor Yellow
docker-compose build --no-cache
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Build failed" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "✓ Build complete" -ForegroundColor Green

Write-Host ""
Write-Host "[4/5] Starting services..." -ForegroundColor Yellow
docker-compose up -d
Write-Host "✓ Services starting..." -ForegroundColor Green

Write-Host ""
Write-Host "[5/5] Waiting for backend to initialize (60 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 60

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Frontend: http://localhost:3001" -ForegroundColor Green
Write-Host "Backend:  http://localhost:8001" -ForegroundColor Green
Write-Host "Health:   http://localhost:8001/health" -ForegroundColor Green
Write-Host ""
Write-Host "Commands:" -ForegroundColor Yellow
Write-Host "  View logs:  docker-compose logs -f" -ForegroundColor Gray
Write-Host "  Stop:       docker-compose down" -ForegroundColor Gray
Write-Host ""
Read-Host "Press Enter to exit"
