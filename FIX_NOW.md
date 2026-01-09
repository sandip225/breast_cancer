# 🔧 Fix Model Corruption - DO THIS NOW

## Problem
```
⚠️ Model file too small (0.0 MB)
```

## Solution - Run This

### Windows PowerShell
```powershell
# Copy and paste this entire block:
docker-compose down; `
docker rmi breast-cancer-backend breast-cancer-frontend; `
docker volume prune -f; `
docker system prune -a -f; `
docker-compose build --no-cache; `
docker-compose up
```

### Windows Command Prompt
```cmd
docker-compose down && ^
docker rmi breast-cancer-backend breast-cancer-frontend && ^
docker volume prune -f && ^
docker system prune -a -f && ^
docker-compose build --no-cache && ^
docker-compose up
```

### Linux / Mac
```bash
docker-compose down && \
docker rmi breast-cancer-backend breast-cancer-frontend && \
docker volume prune -f && \
docker system prune -a -f && \
docker-compose build --no-cache && \
docker-compose up
```

---

## What This Does

1. ✅ Stops containers
2. ✅ Removes old images
3. ✅ Cleans volumes
4. ✅ Cleans Docker system
5. ✅ Rebuilds images (2-3 min)
6. ✅ Starts services

---

## Wait For

- Build to complete (2-3 minutes)
- Backend to start (60 seconds)
- See: "Application startup complete"

---

## Then Verify

```bash
# Check model in container
docker exec breast-cancer-backend ls -lh /app/models/

# Should show: breast_cancer_model.keras (~308 MB)
```

---

## Access

- Frontend: http://localhost:3001
- Backend: http://localhost:8001
- Health: http://localhost:8001/health

---

## Test

1. Open http://localhost:3001
2. Upload image
3. Click Analyze
4. Should work ✅

---

## If Still Broken

```bash
# Check local file
Get-ChildItem -Path "backend/models/breast_cancer_model.keras"

# View logs
docker-compose logs backend

# Check container
docker exec breast-cancer-backend ls -lh /app/models/
```

---

## That's It!

Run the command for your OS and wait. The model corruption issue will be fixed.
