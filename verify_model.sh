#!/bin/bash
# Verify model file is in the correct location

echo "🔍 Verifying model file..."
echo ""

# Check local file
if [ -f "backend/models/breast_cancer_model.keras" ]; then
    SIZE=$(stat -f%z "backend/models/breast_cancer_model.keras" 2>/dev/null || stat -c%s "backend/models/breast_cancer_model.keras" 2>/dev/null)
    SIZE_MB=$((SIZE / 1024 / 1024))
    echo "✅ Local model found: backend/models/breast_cancer_model.keras ($SIZE_MB MB)"
else
    echo "❌ Local model NOT found: backend/models/breast_cancer_model.keras"
    exit 1
fi

echo ""
echo "🐳 Checking Docker container..."

# Check if container is running
if docker ps | grep -q breast-cancer-backend; then
    echo "✅ Backend container is running"
    
    # Check model in container
    if docker exec breast-cancer-backend test -f /app/models/breast_cancer_model.keras; then
        CONTAINER_SIZE=$(docker exec breast-cancer-backend stat -c%s /app/models/breast_cancer_model.keras 2>/dev/null)
        CONTAINER_SIZE_MB=$((CONTAINER_SIZE / 1024 / 1024))
        echo "✅ Model found in container: /app/models/breast_cancer_model.keras ($CONTAINER_SIZE_MB MB)"
    else
        echo "❌ Model NOT found in container: /app/models/breast_cancer_model.keras"
        echo ""
        echo "📋 Container /app/models/ contents:"
        docker exec breast-cancer-backend ls -lh /app/models/ || echo "   (directory doesn't exist)"
        exit 1
    fi
else
    echo "⚠️  Backend container is not running"
    echo "   Run: docker-compose up"
fi

echo ""
echo "✅ All checks passed!"
