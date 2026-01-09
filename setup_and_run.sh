#!/bin/bash

# Setup and run the Breast Cancer Detection System

echo ""
echo "========================================"
echo "Breast Cancer Detection System Setup"
echo "========================================"
echo ""

# Check if model file exists
echo "[1/5] Checking model file..."
if [ -f "backend/models/breast_cancer_model.keras" ]; then
    SIZE=$(stat -f%z "backend/models/breast_cancer_model.keras" 2>/dev/null || stat -c%s "backend/models/breast_cancer_model.keras" 2>/dev/null)
    SIZE_MB=$((SIZE / 1024 / 1024))
    echo "✓ Model found: backend/models/breast_cancer_model.keras ($SIZE_MB MB)"
else
    echo "✗ ERROR: Model file not found at backend/models/breast_cancer_model.keras"
    echo "Please ensure the model file is in the correct location."
    exit 1
fi

echo ""
echo "[2/5] Stopping existing containers..."
docker-compose down 2>/dev/null
echo "✓ Done"

echo ""
echo "[3/5] Building Docker images (this may take a few minutes)..."
docker-compose build --no-cache
if [ $? -ne 0 ]; then
    echo "✗ Build failed"
    exit 1
fi
echo "✓ Build complete"

echo ""
echo "[4/5] Starting services..."
docker-compose up -d
echo "✓ Services starting..."

echo ""
echo "[5/5] Waiting for backend to initialize (60 seconds)..."
sleep 60

echo ""
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "Frontend: http://localhost:3001"
echo "Backend:  http://localhost:8001"
echo "Health:   http://localhost:8001/health"
echo ""
echo "Commands:"
echo "  View logs:  docker-compose logs -f"
echo "  Stop:       docker-compose down"
echo ""
