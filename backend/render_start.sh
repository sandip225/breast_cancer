#!/bin/bash
# Render Backend Start Script

echo "🚀 Starting Breast Cancer Detection Backend..."

# Start uvicorn server using python -m to avoid PATH issues
python -m uvicorn main:app --host 0.0.0.0 --port $PORT

