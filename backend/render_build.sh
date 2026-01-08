#!/bin/bash
# Render Backend Build Script

echo "🚀 Starting Render backend build..."

# Install Python dependencies
echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install --no-cache-dir -r requirements.txt

# Verify uvicorn installation
echo "🔍 Verifying uvicorn installation..."
python -m pip show uvicorn || pip install uvicorn[standard]==0.22.0

echo "✅ Build completed successfully!"

