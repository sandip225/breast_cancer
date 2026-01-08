# Docker Setup Guide

This project includes Docker and Docker Compose configuration for easy deployment and development.

## Prerequisites

- Docker (version 20.10+)
- Docker Compose (version 1.29+)

### Installation

**Windows:**
- Download and install [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop)
- Docker Compose is included with Docker Desktop

**macOS:**
- Download and install [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop)
- Docker Compose is included with Docker Desktop

**Linux:**
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

## Quick Start

### 1. Clone the Repository
```bash
git clone <repository-url>
cd breast-cancer-detection
```

### 2. Prepare Model File
Ensure the model file exists at:
```
backend/models/breast_cancer_model.keras
```

### 3. Build and Run with Docker Compose

**Start all services:**
```bash
docker-compose up --build
```

**Run in background:**
```bash
docker-compose up -d --build
```

**View logs:**
```bash
docker-compose logs -f
```

**View specific service logs:**
```bash
docker-compose logs -f backend
docker-compose logs -f frontend
```

### 4. Access the Application

- **Frontend:** http://localhost:3001
- **Backend API:** http://localhost:8001
- **API Documentation:** http://localhost:8001/docs

### 5. Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Stop and remove all data
docker-compose down -v --remove-orphans
```

## Service Details

### Backend Service
- **Image:** Python 3.11 slim
- **Port:** 8001
- **Framework:** FastAPI
- **Server:** Uvicorn
- **Health Check:** Every 30 seconds
- **Volumes:** 
  - `./backend:/app` - Source code
  - `./backend/models:/app/models` - Model files

### Frontend Service
- **Image:** Node 18 Alpine
- **Port:** 3001
- **Framework:** React
- **Health Check:** Every 30 seconds
- **Volumes:**
  - `./frontend:/app` - Source code
  - `/app/node_modules` - Dependencies (isolated)

## Development Workflow

### Hot Reload
Both services support hot reload during development:

**Backend:** Changes to Python files automatically reload the Uvicorn server
**Frontend:** Changes to React files automatically refresh the browser

### Running Individual Services

**Backend only:**
```bash
docker-compose up backend
```

**Frontend only:**
```bash
docker-compose up frontend
```

### Rebuilding Services

**Rebuild all:**
```bash
docker-compose build --no-cache
```

**Rebuild specific service:**
```bash
docker-compose build --no-cache backend
docker-compose build --no-cache frontend
```

## Environment Variables

### Backend
- `PYTHONUNBUFFERED=1` - Unbuffered Python output
- `MODEL_PATH=/app/models/breast_cancer_model.keras` - Path to ML model

### Frontend
- `REACT_APP_API_BASE_URL=http://backend:8001` - Backend API URL
- `PORT=3001` - Frontend port

## Troubleshooting

### Port Already in Use
If ports 3001 or 8001 are already in use:

```bash
# Change ports in docker-compose.yml
# For example, change "3001:3001" to "3002:3001"
```

### Model File Not Found
Ensure the model file exists:
```bash
ls -la backend/models/breast_cancer_model.keras
```

### Backend Health Check Failing
Check backend logs:
```bash
docker-compose logs backend
```

### Frontend Not Connecting to Backend
Verify the API URL in frontend environment:
```bash
docker-compose logs frontend | grep API
```

### Clear Everything and Start Fresh
```bash
docker-compose down -v --remove-orphans
docker system prune -a
docker-compose up --build
```

## Production Deployment

For production, modify `docker-compose.yml`:

1. Remove `--reload` flag from backend command
2. Set `REACT_APP_API_BASE_URL` to production backend URL
3. Use production-grade reverse proxy (nginx)
4. Enable HTTPS/SSL
5. Set appropriate resource limits
6. Use environment files for secrets

Example production command:
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## Useful Commands

```bash
# View running containers
docker-compose ps

# Execute command in container
docker-compose exec backend python -c "import tensorflow; print(tensorflow.__version__)"

# View container resource usage
docker stats

# Inspect service configuration
docker-compose config

# Validate docker-compose file
docker-compose config --quiet

# Remove unused images
docker image prune -a

# View network details
docker network inspect breast-cancer-network
```

## Performance Tips

1. **Use .dockerignore files** - Already configured to exclude unnecessary files
2. **Layer caching** - Dependencies are installed before copying code
3. **Alpine images** - Frontend uses Alpine for smaller image size
4. **Volume mounts** - Development uses volumes for hot reload
5. **Health checks** - Automatic service restart on failure

## Security Considerations

1. Never commit `.env` files with secrets
2. Use environment variables for sensitive data
3. Implement API authentication in production
4. Use HTTPS in production
5. Regularly update base images
6. Scan images for vulnerabilities: `docker scan <image-name>`

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [FastAPI Docker Guide](https://fastapi.tiangolo.com/deployment/docker/)
- [React Docker Guide](https://create-react-app.dev/deployment/)
