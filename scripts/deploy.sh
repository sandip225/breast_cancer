#!/bin/bash
# Deployment script for breast cancer detection system

set -e

echo "🚀 Starting deployment..."

# Configuration
PROJECT_DIR="${PROJECT_DIR:-/home/ubuntu/breast_cancer}"
COMPOSE_FILE="${PROJECT_DIR}/docker-compose.prod.yml"

cd "$PROJECT_DIR"

# Pull latest code
echo "📥 Pulling latest code..."
git pull origin main

# Pull latest Docker images
echo "📦 Pulling Docker images..."
docker compose -f "$COMPOSE_FILE" pull

# Stop old containers
echo "🛑 Stopping old containers..."
docker compose -f "$COMPOSE_FILE" down

# Start new containers
echo "🚀 Starting new containers..."
docker compose -f "$COMPOSE_FILE" up -d

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 30

# Health check
echo "🔍 Running health check..."
if curl -f http://localhost:8001/health > /dev/null 2>&1; then
    echo "✅ Backend is healthy"
else
    echo "❌ Backend health check failed"
    docker compose -f "$COMPOSE_FILE" logs backend
    exit 1
fi

if curl -f http://localhost:3001 > /dev/null 2>&1; then
    echo "✅ Frontend is healthy"
else
    echo "❌ Frontend health check failed"
    docker compose -f "$COMPOSE_FILE" logs frontend
    exit 1
fi

# Clean up old images
echo "🧹 Cleaning up old images..."
docker image prune -f

echo ""
echo "✅ Deployment completed successfully!"
echo "📍 Backend: http://localhost:8001"
echo "📍 Frontend: http://localhost:3001"
echo "📍 API Docs: http://localhost:8001/docs"
