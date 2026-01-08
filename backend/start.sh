#!/bin/bash
# Render.com Startup Script
# This script runs when your app starts on Render

echo "🚀 Starting Breast Cancer Detection Backend..."

# Check if model exists (should be present via Git LFS)
echo "📥 Checking for model file..."

MODEL_FILE="models/breast_cancer_model.keras"
MIN_SIZE=100000000  # 100 MB minimum

if [ -f "$MODEL_FILE" ]; then
    FILE_SIZE=$(stat -f%z "$MODEL_FILE" 2>/dev/null || stat -c%s "$MODEL_FILE" 2>/dev/null)
    MODEL_SIZE=$(du -h "$MODEL_FILE" | cut -f1)
    echo "✅ Model file found! (Size: $MODEL_SIZE)"
    
    # Check if it's actually the model or just a Git LFS pointer
    if [ "$FILE_SIZE" -lt "$MIN_SIZE" ]; then
        echo "⚠️  File is too small ($MODEL_SIZE) - likely a Git LFS pointer"
        echo "📥 Attempting to download model..."
        python download_model.py
    fi
else
    echo "⚠️  Model file not found via Git LFS"
    echo "📥 Attempting to download model..."
    python download_model.py
fi

# Final check
if [ -f "$MODEL_FILE" ]; then
    FILE_SIZE=$(stat -f%z "$MODEL_FILE" 2>/dev/null || stat -c%s "$MODEL_FILE" 2>/dev/null)
    if [ "$FILE_SIZE" -gt "$MIN_SIZE" ]; then
        echo "✅ Model ready! Starting server..."
    else
        echo "❌ ERROR: Model file invalid (too small)"
        exit 1
    fi
else
    echo "❌ ERROR: Model file not available"
    echo "   Please configure one of: HF_MODEL_REPO, MODEL_URL, or GDRIVE_FILE_ID"
    exit 1
fi

# Start the FastAPI server
echo "🌐 Starting FastAPI server on port ${PORT:-8000}..."
uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}

