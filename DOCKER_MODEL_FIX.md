# Docker Model File Fix

## Issue
Backend error: `Model file not found at /app/models/breast_cancer_model.keras`

## Root Cause
The model file wasn't being properly copied into the Docker image during the build process.

## Solution Applied

### 1. Updated Dockerfile
Added explicit model file copy:
```dockerfile
# Copy model file explicitly (ensure it's included)
COPY models/breast_cancer_model.keras /app/models/breast_cancer_model.keras
```

### 2. Updated docker-compose.yml
Added read-only volume mount:
```yaml
volumes:
  - ./backend:/app
  - ./backend/models:/app/models:ro
```

### 3. Enhanced Error Logging
Updated `main.py` to show detailed diagnostics when model is missing.

---

## How to Fix

### Option 1: Automatic Setup (Recommended)

**Windows (PowerShell):**
```powershell
.\setup_and_run.ps1
```

**Windows (Command Prompt):**
```cmd
setup_and_run.bat
```

**Linux/Mac:**
```bash
bash setup_and_run.sh
```

### Option 2: Manual Setup

```bash
# 1. Verify model exists
Get-ChildItem -Path "backend/models/breast_cancer_model.keras"

# 2. Stop and remove old containers
docker-compose down
docker rmi breast-cancer-backend breast-cancer-frontend

# 3. Rebuild without cache
docker-compose build --no-cache

# 4. Start services
docker-compose up

# 5. Wait 60 seconds for backend to initialize

# 6. Verify model is loaded
curl http://localhost:8001/health
```

---

## Verification

### Check 1: Local File
```bash
Get-ChildItem -Path "backend/models/breast_cancer_model.keras"
# Should show: breast_cancer_model.keras (~308 MB)
```

### Check 2: Docker Build
```bash
docker-compose build --no-cache
# Should complete without "COPY failed" errors
```

### Check 3: Container File
```bash
docker exec breast-cancer-backend ls -lh /app/models/
# Should show: breast_cancer_model.keras (~308 MB)
```

### Check 4: Backend Health
```bash
curl http://localhost:8001/health
# Should show: "model_status": "loaded"
```

### Check 5: Upload Test
1. Go to http://localhost:3001
2. Upload a mammogram image
3. Should analyze without model errors

---

## File Structure

```
breast_cancer/
├── backend/
│   ├── models/
│   │   └── breast_cancer_model.keras  ← Model file (308 MB)
│   ├── Dockerfile                      ← Updated with explicit COPY
│   ├── main.py                         ← Enhanced error logging
│   ├── requirements.txt
│   └── ...
├── frontend/
│   └── ...
├── docker-compose.yml                  ← Updated with volume mount
├── setup_and_run.ps1                   ← PowerShell setup script
├── setup_and_run.bat                   ← Batch setup script
└── ...
```

---

## Key Changes

| File | Change |
|------|--------|
| `backend/Dockerfile` | Added `COPY models/breast_cancer_model.keras /app/models/breast_cancer_model.keras` |
| `docker-compose.yml` | Added volume mount `./backend/models:/app/models:ro` |
| `backend/main.py` | Enhanced `check_model_exists()` with detailed logging |
| `backend/.env` | Removed Hugging Face references |
| `backend/requirements.txt` | Removed `huggingface-hub` |

---

## Troubleshooting

### Model Still Not Found After Setup

**Step 1: Check local file**
```bash
Get-ChildItem -Path "backend/models/breast_cancer_model.keras"
```
If not found, you need to obtain the model file.

**Step 2: Check Docker logs**
```bash
docker-compose logs backend
```
Look for error messages about model loading.

**Step 3: Manually verify in container**
```bash
docker exec breast-cancer-backend ls -lh /app/models/
```

**Step 4: Force copy model into running container**
```bash
docker cp backend/models/breast_cancer_model.keras breast-cancer-backend:/app/models/
docker-compose restart backend
```

### Build Fails with "COPY failed"

This means the model file isn't in the build context.

**Solution:**
1. Verify file exists: `Get-ChildItem -Path "backend/models/breast_cancer_model.keras"`
2. Check `.dockerignore` doesn't exclude models: `Get-Content backend/.dockerignore`
3. Rebuild: `docker-compose build --no-cache`

### Container Starts but Model Not Loaded

Check the backend logs:
```bash
docker-compose logs backend | grep -i model
```

Expected output:
```
✅ Model exists (308.0 MB) at /app/models/breast_cancer_model.keras
```

---

## Performance Notes

- Model file: ~308 MB
- First build: 5-10 minutes (depends on internet speed)
- Subsequent builds: 1-2 minutes
- Backend startup: 30-60 seconds (model loading)
- Analysis time: 10-30 seconds per image

---

## Support

If issues persist:

1. **Check Docker installation**: `docker --version`
2. **Check Docker Compose**: `docker-compose --version`
3. **View full logs**: `docker-compose logs`
4. **Rebuild everything**: `docker-compose down && docker-compose build --no-cache && docker-compose up`
5. **Check disk space**: Ensure at least 2 GB free space

---

## Next Steps

After successful setup:

1. Open http://localhost:3001 in your browser
2. Login with your credentials
3. Upload a mammogram image
4. View analysis results
5. Download PDF report if needed

Enjoy using the Breast Cancer Detection System!
