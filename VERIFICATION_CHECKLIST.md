# Verification Checklist - Model Fix

## Pre-Setup Verification

- [ ] Model file exists
  ```bash
  Get-ChildItem -Path "backend/models/breast_cancer_model.keras"
  ```
  Expected: File ~308 MB

- [ ] Docker installed
  ```bash
  docker --version
  ```
  Expected: Docker version 20.10+

- [ ] Docker Compose installed
  ```bash
  docker-compose --version
  ```
  Expected: Docker Compose version 1.29+

- [ ] Disk space available
  ```bash
  # Windows: Get-Volume
  # Linux/Mac: df -h
  ```
  Expected: At least 2 GB free

---

## Setup Execution

- [ ] Run setup script
  - Windows PowerShell: `.\setup_and_run.ps1`
  - Windows CMD: `setup_and_run.bat`
  - Linux/Mac: `./setup_and_run.sh`

- [ ] Script completes without errors

- [ ] Wait 60 seconds for backend initialization

---

## Post-Setup Verification

### 1. Check Model File in Container
```bash
docker exec breast-cancer-backend ls -lh /app/models/
```
Expected output:
```
-rw-r--r-- 1 root root 308M Jan  9 13:57 breast_cancer_model.keras
```

- [ ] Model file exists in container
- [ ] File size is ~308 MB
- [ ] File is readable

### 2. Check Backend Health
```bash
curl http://localhost:8001/health
```
Expected response:
```json
{
  "status": "ok",
  "model_status": "loaded",
  "model_error": null,
  "model_path": "/app/models/breast_cancer_model.keras"
}
```

- [ ] Status is "ok"
- [ ] Model status is "loaded"
- [ ] No model error
- [ ] Model path is correct

### 3. Check Backend Logs
```bash
docker-compose logs backend | grep -i model
```
Expected output:
```
✅ Model exists (308.0 MB) at /app/models/breast_cancer_model.keras
```

- [ ] Model loading message appears
- [ ] No error messages
- [ ] Application startup complete

### 4. Check Frontend
Open http://localhost:3001 in browser

- [ ] Page loads without errors
- [ ] Logo displays in header
- [ ] Upload section visible
- [ ] No console errors (F12 to check)

### 5. Check Backend API
Open http://localhost:8001/docs in browser

- [ ] Swagger UI loads
- [ ] API endpoints visible
- [ ] /health endpoint available
- [ ] /analyze endpoint available
- [ ] /report endpoint available

---

## Functional Testing

### Test 1: Image Upload
1. Go to http://localhost:3001
2. Click "Browse File" or drag & drop
3. Select a mammogram image
4. Click "Analyze"

- [ ] File uploads successfully
- [ ] No model error appears
- [ ] Analysis starts

### Test 2: Analysis Results
After analysis completes:

- [ ] Results display without errors
- [ ] Prediction metrics show (Benign %, Malignant %)
- [ ] Risk level displays
- [ ] Visual tabs work (Overlay, Heatmap, BBox, Cancer Type)
- [ ] Images load correctly

### Test 3: Report Generation
1. After analysis, click "Download Report"
2. PDF should download

- [ ] Report button works
- [ ] PDF downloads successfully
- [ ] PDF opens and displays correctly

### Test 4: Multiple Uploads
1. Upload another image
2. Analyze
3. Check results

- [ ] Second analysis works
- [ ] No model errors
- [ ] Results are different from first image

---

## Docker Verification

### Container Status
```bash
docker-compose ps
```
Expected:
```
NAME                    STATUS
breast-cancer-backend   Up (healthy)
breast-cancer-frontend  Up (healthy)
```

- [ ] Backend container is running
- [ ] Frontend container is running
- [ ] Both show healthy status

### Volume Mount
```bash
docker inspect breast-cancer-backend | grep -A 10 Mounts
```
Expected: Should show mount from `./backend/models` to `/app/models`

- [ ] Volume mount exists
- [ ] Source path is correct
- [ ] Destination path is correct

### Network
```bash
docker network ls | grep breast-cancer
```

- [ ] Network exists
- [ ] Both containers connected

---

## Performance Verification

### Backend Response Time
```bash
time curl http://localhost:8001/health
```

- [ ] Response time < 1 second
- [ ] No timeouts

### Image Analysis Time
Upload an image and measure time:

- [ ] Analysis completes in 10-30 seconds
- [ ] No timeout errors
- [ ] Results are accurate

---

## Error Handling

### Test Missing Model (Intentional)
```bash
# Temporarily rename model
docker exec breast-cancer-backend mv /app/models/breast_cancer_model.keras /app/models/breast_cancer_model.keras.bak

# Try to analyze
# Should show clear error message

# Restore model
docker exec breast-cancer-backend mv /app/models/breast_cancer_model.keras.bak /app/models/breast_cancer_model.keras
```

- [ ] Error message is clear
- [ ] Error message shows expected path
- [ ] Error message shows what's in directory

### Test Invalid Image
Upload a non-image file:

- [ ] Backend rejects with clear error
- [ ] Frontend shows error message
- [ ] No crash or hang

---

## Cleanup & Restart

### Stop Services
```bash
docker-compose down
```

- [ ] Containers stop gracefully
- [ ] No errors during shutdown

### Restart Services
```bash
docker-compose up
```

- [ ] Containers start successfully
- [ ] Model loads again
- [ ] Health check passes

---

## Final Checklist

- [ ] All pre-setup checks passed
- [ ] Setup script completed successfully
- [ ] Model file verified in container
- [ ] Backend health check passed
- [ ] Frontend loads correctly
- [ ] Image upload works
- [ ] Analysis completes without errors
- [ ] Results display correctly
- [ ] Report generation works
- [ ] Multiple uploads work
- [ ] Docker containers healthy
- [ ] Volume mount correct
- [ ] Error handling works
- [ ] Services restart successfully

---

## Success Criteria

✅ **All checks passed** = System is working correctly

If any check fails:
1. Review the specific section
2. Check logs: `docker-compose logs`
3. Rebuild: `docker-compose build --no-cache`
4. Restart: `docker-compose up`

---

## Support

If verification fails:
- Check `FIX_INSTRUCTIONS.md` for quick fixes
- Check `MODEL_SETUP_GUIDE.md` for detailed troubleshooting
- Check `DOCKER_MODEL_FIX.md` for technical details
- View logs: `docker-compose logs backend`
- Check container: `docker exec breast-cancer-backend ls -lh /app/models/`

---

## Sign-Off

Date: _______________
Verified By: _______________
Status: ✅ PASSED / ❌ FAILED

Notes: _______________________________________________
