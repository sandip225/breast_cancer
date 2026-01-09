# Model Setup Guide

## Problem
The backend shows error: "Model file not found at /app/models/breast_cancer_model.keras"

## Solution

### Step 1: Verify Local Model File
The model file should be at: `backend/models/breast_cancer_model.keras`

Check if it exists:
```bash
# Windows PowerShell
Get-ChildItem -Path "backend/models/"

# Linux/Mac
ls -lh backend/models/
```

Expected output: `breast_cancer_model.keras` (~308 MB)

### Step 2: Clean Docker Build
Remove old containers and rebuild:

```bash
# Stop running containers
docker-compose down

# Remove old images
docker rmi breast-cancer-backend breast-cancer-frontend

# Rebuild with no cache
docker-compose build --no-cache

# Start services
docker-compose up
```

### Step 3: Verify Model in Container
After containers are running, verify the model is copied:

```bash
# Check if model exists in container
docker exec breast-cancer-backend ls -lh /app/models/

# Expected output:
# -rw-r--r-- 1 root root 308M Jan  9 13:57 breast_cancer_model.keras
```

### Step 4: Check Backend Health
```bash
# Check backend health endpoint
curl http://localhost:8001/health

# Expected response:
# {
#   "status": "ok",
#   "model_status": "loaded",
#   "model_error": null,
#   "model_path": "/app/models/breast_cancer_model.keras"
# }
```

### Step 5: Test Upload
1. Go to http://localhost:3001
2. Upload a mammogram image
3. Should analyze without model errors

---

## Troubleshooting

### Model Still Not Found

**Check 1: Verify file exists locally**
```bash
Get-ChildItem -Path "backend/models/breast_cancer_model.keras"
```

**Check 2: Verify Docker volume mount**
```bash
docker inspect breast-cancer-backend | grep -A 10 Mounts
```

Should show:
```
"Mounts": [
    {
        "Type": "bind",
        "Source": "/path/to/breast_cancer/backend/models",
        "Destination": "/app/models",
        ...
    }
]
```

**Check 3: View container logs**
```bash
docker-compose logs backend
```

Look for lines like:
```
✅ Model exists (308.0 MB) at /app/models/breast_cancer_model.keras
```

**Check 4: Manually copy model into running container**
```bash
docker cp backend/models/breast_cancer_model.keras breast-cancer-backend:/app/models/
```

Then restart:
```bash
docker-compose restart backend
```

### Docker Build Fails

If you see: `COPY failed: file not found in build context`

This means the model file isn't being included in the build. Try:

```bash
# Verify file exists
Get-ChildItem -Path "backend/models/breast_cancer_model.keras"

# Check .dockerignore doesn't exclude models
Get-Content backend/.dockerignore

# Rebuild
docker-compose build --no-cache
```

---

## File Locations

| File | Location | Size |
|------|----------|------|
| Model | `backend/models/breast_cancer_model.keras` | ~308 MB |
| Docker | `backend/Dockerfile` | - |
| Compose | `docker-compose.yml` | - |
| Backend | `backend/main.py` | - |
| Frontend | `frontend/src/AppContent.js` | - |

---

## Key Changes Made

1. **Dockerfile**: Added explicit `COPY models/breast_cancer_model.keras /app/models/breast_cancer_model.keras`
2. **docker-compose.yml**: Added volume mount `./backend/models:/app/models:ro`
3. **main.py**: Enhanced error logging to show what's in the models directory
4. **startup.sh**: Added diagnostics script

---

## Quick Start

```bash
# 1. Verify model exists
Get-ChildItem -Path "backend/models/breast_cancer_model.keras"

# 2. Build and start
docker-compose build --no-cache
docker-compose up

# 3. Wait for backend to start (60 seconds)
# 4. Check health
curl http://localhost:8001/health

# 5. Open frontend
# http://localhost:3001
```

---

## Still Having Issues?

1. Check Docker logs: `docker-compose logs backend`
2. Verify model file: `Get-ChildItem -Path "backend/models/"`
3. Check container: `docker exec breast-cancer-backend ls -lh /app/models/`
4. Rebuild: `docker-compose build --no-cache && docker-compose up`
