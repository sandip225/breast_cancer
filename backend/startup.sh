#!/bin/bash
# Startup script to ensure model is available

echo "🔍 Checking for model file..."

MODEL_PATH="${MODEL_PATH:-/app/models/breast_cancer_model.keras}"
MODELS_DIR=$(dirname "$MODEL_PATH")

# Create models directory if it doesn't exist
mkdir -p "$MODELS_DIR"

# Check if model exists
if [ -f "$MODEL_PATH" ]; then
    SIZE=$(stat -f%z "$MODEL_PATH" 2>/dev/null || stat -c%s "$MODEL_PATH" 2>/dev/null)
    SIZE_MB=$((SIZE / 1024 / 1024))
    echo "✅ Model found at $MODEL_PATH ($SIZE_MB MB)"
else
    echo "⚠️  Model not found at $MODEL_PATH"
    echo "   Checking directory contents:"
    ls -lh "$MODELS_DIR" 2>/dev/null || echo "   Directory is empty"
fi

# Start the application
echo "🚀 Starting FastAPI application..."
python -m uvicorn main:app --host 0.0.0.0 --port 8001

