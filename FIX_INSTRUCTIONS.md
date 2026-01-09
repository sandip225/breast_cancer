# Fix Instructions - Model File Not Found Error

## Quick Fix (5 minutes)

### Windows Users

**Option 1: PowerShell (Recommended)**
```powershell
# Run this command in PowerShell
.\setup_and_run.ps1
```

**Option 2: Command Prompt**
```cmd
# Run this command in Command Prompt
setup_and_run.bat
```

### Linux/Mac Users

```bash
# Make script executable
chmod +x setup_and_run.sh

# Run setup
./setup_and_run.sh
```

---

## What the Script Does

1. ✅ Verifies model file exists (308 MB)
2. ✅ Stops old Docker containers
3. ✅ Removes old Docker images
4. ✅ Rebuilds Docker images with model file
5. ✅ Starts backend and frontend services
6. ✅ Waits 60 seconds for backend initialization
7. ✅ Shows you the URLs to access the application

---

## Manual Fix (If Script Doesn't Work)

### Step 1: Verify Model File
```bash
# Windows PowerShell
Get-ChildItem -Path "backend/models/breast_cancer_model.keras"

# Linux/Mac
ls -lh backend/models/breast_cancer_model.keras
```

**Expected:** File should be ~308 MB

If file doesn't exist, you need to obtain the model file first.

### Step 2: Stop Old Containers
```bash
docker-compose down
```

### Step 3: Remove Old Images
```bash
docker rmi breast-cancer-backend breast-cancer-frontend
```

### Step 4: Rebuild Without Cache
```bash
docker-compose build --no-cache
```

This will take 5-10 minutes. Wait for it to complete.

### Step 5: Start Services
```bash
docker-compose up
```

Wait for the backend to start (you'll see "Application startup complete").

### Step 6: Verify in Another Terminal
```bash
# Check if model is loaded
curl http://localhost:8001/health

# Expected response:
# {
#   "status": "ok",
#   "model_status": "loaded",
#   "model_error": null,
#   "model_path": "/app/models/breast_cancer_model.keras"
# }
```

---

## Access the Application

Once setup is complete:

- **Frontend**: http://localhost:3001
- **Backend API**: http://localhost:8001
- **API Docs**: http://localhost:8001/docs
- **Health Check**: http://localhost:8001/health

---

## Troubleshooting

### Issue: "Model file not found" error still appears

**Solution 1: Check if model exists locally**
```bash
Get-ChildItem -Path "backend/models/breast_cancer_model.keras"
```

If not found, you need to obtain the model file.

**Solution 2: Check Docker logs**
```bash
docker-compose logs backend
```

Look for lines like:
```
✅ Model exists (308.0 MB) at /app/models/breast_cancer_model.keras
```

**Solution 3: Verify model in container**
```bash
docker exec breast-cancer-backend ls -lh /app/models/
```

Should show: `breast_cancer_model.keras` (~308 MB)

**Solution 4: Force copy model into container**
```bash
docker cp backend/models/breast_cancer_model.keras breast-cancer-backend:/app/models/
docker-compose restart backend
```

### Issue: Docker build fails

**Solution:**
```bash
# Clean everything
docker-compose down
docker system prune -a

# Rebuild
docker-compose build --no-cache
docker-compose up
```

### Issue: Port already in use

If you see "Address already in use":

```bash
# Stop all containers
docker-compose down

# Or kill specific ports
# Windows: netstat -ano | findstr :8001
# Linux/Mac: lsof -i :8001
```

### Issue: Out of disk space

The model file is 308 MB. Ensure you have at least 2 GB free space.

```bash
# Check disk space
# Windows: Get-Volume
# Linux/Mac: df -h
```

---

## What Changed

The following files were updated to fix the model loading issue:

1. **`backend/Dockerfile`** - Added explicit model file copy
2. **`docker-compose.yml`** - Added volume mount for models
3. **`backend/main.py`** - Enhanced error logging
4. **`backend/.env`** - Removed Hugging Face references
5. **`backend/requirements.txt`** - Removed huggingface-hub

New files created:
- `setup_and_run.ps1` - PowerShell setup script
- `setup_and_run.bat` - Batch setup script
- `setup_and_run.sh` - Bash setup script
- `MODEL_SETUP_GUIDE.md` - Detailed troubleshooting guide
- `DOCKER_MODEL_FIX.md` - Technical explanation

---

## Testing the Fix

After setup completes:

1. Open http://localhost:3001 in your browser
2. Login with your credentials
3. Upload a mammogram image
4. Click "Analyze"
5. Should see results without model errors
6. Try downloading the PDF report

---

## Performance

- **First build**: 5-10 minutes (downloads dependencies)
- **Subsequent builds**: 1-2 minutes
- **Backend startup**: 30-60 seconds (loads model)
- **Image analysis**: 10-30 seconds per image

---

## Still Having Issues?

1. **Check Docker installation**
   ```bash
   docker --version
   docker-compose --version
   ```

2. **View full logs**
   ```bash
   docker-compose logs
   ```

3. **Rebuild everything**
   ```bash
   docker-compose down
   docker system prune -a
   docker-compose build --no-cache
   docker-compose up
   ```

4. **Check model file**
   ```bash
   Get-ChildItem -Path "backend/models/breast_cancer_model.keras"
   ```

---

## Success Indicators

✅ Setup script completes without errors
✅ Docker images build successfully
✅ Containers start and stay running
✅ Backend health check shows "model_status": "loaded"
✅ Frontend loads at http://localhost:3001
✅ Image upload works without model errors
✅ Analysis results display correctly

---

## Next Steps

1. Run the setup script
2. Wait for services to start
3. Open http://localhost:3001
4. Test with a mammogram image
5. Verify analysis works

The model loading issue should now be completely resolved!

---

## Support

For additional help:
- Check `MODEL_SETUP_GUIDE.md` for detailed troubleshooting
- Check `DOCKER_MODEL_FIX.md` for technical details
- View Docker logs: `docker-compose logs backend`
- Check container: `docker exec breast-cancer-backend ls -lh /app/models/`
