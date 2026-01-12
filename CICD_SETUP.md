# CI/CD Pipeline Setup Guide

## Overview

This project uses GitHub Actions for automated CI/CD pipeline:

```
Push to main → Test → Build Docker Images → Deploy to Server
```

## Pipeline Stages

| Stage | Description |
|-------|-------------|
| **Test Backend** | Run Python tests, check database connection |
| **Test Frontend** | Install dependencies, lint, build |
| **Build Backend** | Build & push Docker image to Docker Hub |
| **Build Frontend** | Build & push Docker image to Docker Hub |
| **Deploy** | SSH to server, pull images, restart containers |

---

## Setup Instructions

### Step 1: Create Docker Hub Account

1. Go to https://hub.docker.com
2. Create an account
3. Create access token: Account Settings → Security → New Access Token

### Step 2: Add GitHub Secrets

Go to your GitHub repo → Settings → Secrets and variables → Actions → New repository secret

Add these secrets:

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `DOCKER_USERNAME` | your-dockerhub-username | Docker Hub username |
| `DOCKER_PASSWORD` | your-access-token | Docker Hub access token |
| `SERVER_HOST` | 18.191.185.246 | Your Ubuntu server IP |
| `SERVER_USERNAME` | ubuntu | SSH username |
| `SERVER_SSH_KEY` | (paste private key) | SSH private key content |
| `API_BASE_URL` | http://18.191.185.246:8001 | Backend API URL |
| `SECRET_KEY` | your-secret-key | JWT secret key |

### Step 3: Setup SSH Key

On your local machine:

```bash
# Generate SSH key (if not exists)
ssh-keygen -t rsa -b 4096 -C "github-actions"

# Copy public key to server
ssh-copy-id -i ~/.ssh/id_rsa.pub ubuntu@18.191.185.246

# Copy private key content for GitHub secret
cat ~/.ssh/id_rsa
```

Paste the private key content into `SERVER_SSH_KEY` secret.

### Step 4: Prepare Server

SSH into your Ubuntu server:

```bash
ssh ubuntu@18.191.185.246

# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker ubuntu

# Install Docker Compose
sudo apt-get update
sudo apt-get install docker-compose-plugin

# Create project directory
mkdir -p ~/breast_cancer
cd ~/breast_cancer

# Clone repository
git clone https://github.com/YOUR_USERNAME/breast_cancer.git .

# Create models directory
mkdir -p /home/ubuntu/models

# Copy model file (from your local machine)
# scp backend/models/breast_cancer_model.keras ubuntu@18.191.185.246:/home/ubuntu/models/

# Create .env file
cat > .env << EOF
DOCKER_USERNAME=your-dockerhub-username
DB_USER=bcuser
DB_PASSWORD=your-secure-password
DB_NAME=breast_cancer_db
API_BASE_URL=http://18.191.185.246:8001
SECRET_KEY=your-super-secret-key
EOF

# Make deploy script executable
chmod +x scripts/deploy.sh
```

### Step 5: Test Pipeline

1. Make a small change to your code
2. Commit and push to main branch:

```bash
git add .
git commit -m "Test CI/CD pipeline"
git push origin main
```

3. Go to GitHub → Actions tab → Watch the pipeline run

---

## Pipeline Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                     Push to main branch                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                         TEST STAGE                           │
├─────────────────────────────┬───────────────────────────────┤
│      Test Backend           │       Test Frontend            │
│  - Setup Python 3.10        │  - Setup Node.js 18            │
│  - Install dependencies     │  - npm install                 │
│  - Run database tests       │  - npm run lint                │
│                             │  - npm run build               │
└─────────────────────────────┴───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        BUILD STAGE                           │
├─────────────────────────────┬───────────────────────────────┤
│     Build Backend Image     │    Build Frontend Image        │
│  - Docker build             │  - Docker build                │
│  - Push to Docker Hub       │  - Push to Docker Hub          │
│  - Tag: latest, sha         │  - Tag: latest, sha            │
└─────────────────────────────┴───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                       DEPLOY STAGE                           │
│  - SSH to Ubuntu server                                      │
│  - git pull origin main                                      │
│  - docker compose pull                                       │
│  - docker compose down                                       │
│  - docker compose up -d                                      │
│  - Health check                                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    DEPLOYMENT COMPLETE                       │
│  - Backend: http://18.191.185.246:8001                      │
│  - Frontend: http://18.191.185.246:3001                     │
└─────────────────────────────────────────────────────────────┘
```

---

## Manual Deployment

If you need to deploy manually:

```bash
ssh ubuntu@18.191.185.246
cd ~/breast_cancer
./scripts/deploy.sh
```

---

## Troubleshooting

### Pipeline fails at Test stage

Check the logs in GitHub Actions. Common issues:
- Missing dependencies in requirements.txt
- Database connection issues

### Pipeline fails at Build stage

- Check Docker Hub credentials
- Verify DOCKER_USERNAME and DOCKER_PASSWORD secrets

### Pipeline fails at Deploy stage

- Check SSH key is correct
- Verify server is accessible
- Check server has Docker installed

### View logs on server

```bash
ssh ubuntu@18.191.185.246
cd ~/breast_cancer
docker compose logs backend
docker compose logs frontend
```

---

## Files Structure

```
breast_cancer/
├── .github/
│   └── workflows/
│       └── ci-cd.yml          # GitHub Actions workflow
├── scripts/
│   └── deploy.sh              # Deployment script
├── backend/
│   ├── Dockerfile
│   └── ...
├── frontend/
│   ├── Dockerfile
│   └── ...
├── docker-compose.yml         # Development
├── docker-compose.prod.yml    # Production
├── .env.production.example    # Environment template
└── CICD_SETUP.md             # This file
```

---

## Security Notes

1. Never commit `.env` files to Git
2. Use strong passwords for database
3. Rotate secrets periodically
4. Use HTTPS in production (add nginx/traefik)

---

## Next Steps

1. Add HTTPS with Let's Encrypt
2. Add monitoring (Prometheus/Grafana)
3. Add backup for database
4. Add staging environment
