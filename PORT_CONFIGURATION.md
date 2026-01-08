# Port Configuration Guide

## Current Running Ports

### Frontend (React)
- **Port:** 3001 (primary) / 3002 (fallback)
- **Status:** ✅ Running
- **Access:** http://localhost:3001
- **Configuration:** `frontend/package.json` - `"start": "set PORT=3001 && react-scripts start"`
- **Process:** Node.js
- **What it does:** Serves the React UI for image upload and analysis

### Backend (FastAPI)
- **Port:** 8001
- **Status:** ✅ Running
- **Access:** http://localhost:8001
- **Configuration:** `backend/main.py` - Last line shows `# uvicorn main:app --reload --port 8000` (comment, actual port is 8001)
- **Process:** Python (Uvicorn server)
- **What it does:** Handles image analysis, ML model predictions, PDF report generation
- **API Docs:** http://localhost:8001/docs

### Database Services
- **PostgreSQL:** Port 5432 (running)
- **MongoDB:** Port 27017 (running)
- **Note:** Currently NOT used by the application (no database integration yet)

---

## How to Start Services

### Option 1: Manual Start (Development)

**Terminal 1 - Backend:**
```bash
cd backend
.\venv\Scripts\activate
python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm start
```

### Option 2: Docker Compose (Recommended)

```bash
docker-compose up --build
```

This automatically starts:
- Backend on port 8001
- Frontend on port 3001

### Option 3: Individual Docker Containers

**Backend:**
```bash
docker build -t breast-cancer-backend ./backend
docker run -p 8001:8001 breast-cancer-backend
```

**Frontend:**
```bash
docker build -t breast-cancer-frontend ./frontend
docker run -p 3001:3001 breast-cancer-frontend
```

---

## Port Mapping Summary

| Service | Port | Type | Status | Access |
|---------|------|------|--------|--------|
| Frontend (React) | 3001 | HTTP | ✅ Running | http://localhost:3001 |
| Frontend (Fallback) | 3002 | HTTP | ✅ Running | http://localhost:3002 |
| Backend (FastAPI) | 8001 | HTTP | ✅ Running | http://localhost:8001 |
| Backend API Docs | 8001 | HTTP | ✅ Running | http://localhost:8001/docs |
| PostgreSQL | 5432 | TCP | ✅ Running | localhost:5432 |
| MongoDB | 27017 | TCP | ✅ Running | localhost:27017 |

---

## Communication Flow

```
User Browser (http://localhost:3001)
        ↓
    Frontend (React)
        ↓
    API Call to Backend
        ↓
Backend (FastAPI) on port 8001
        ↓
    ML Model Processing
        ↓
    Response back to Frontend
        ↓
    Display Results
```

---

## Changing Ports

### Change Frontend Port

**Option 1: Modify package.json**
```json
"start": "set PORT=3002 && react-scripts start"
```

**Option 2: Set environment variable**
```bash
set PORT=3002
npm start
```

### Change Backend Port

**Option 1: Command line**
```bash
python -m uvicorn main:app --port 9000
```

**Option 2: Docker Compose**
Edit `docker-compose.yml`:
```yaml
backend:
  ports:
    - "9000:8001"  # Change 9000 to your desired port
```

**Option 3: Update frontend API URL**
If you change backend port, update `frontend/src/AppContent.js`:
```javascript
const getDefaultApiBase = () => {
  if (typeof window !== "undefined") {
    const localHosts = ["localhost", "127.0.0.1", "0.0.0.0"];
    if (localHosts.includes(window.location.hostname)) {
      return "http://localhost:9000";  // Change to new port
    }
  }
  // ... rest of code
};
```

---

## Troubleshooting

### Port Already in Use

**Find what's using the port:**
```bash
netstat -ano | findstr :3001
netstat -ano | findstr :8001
```

**Kill the process (Windows):**
```bash
taskkill /PID <PID> /F
```

**Kill the process (Linux/Mac):**
```bash
lsof -ti:3001 | xargs kill -9
lsof -ti:8001 | xargs kill -9
```

### Backend Not Responding

1. Check if backend is running:
   ```bash
   curl http://localhost:8001/health
   ```

2. Check logs:
   ```bash
   docker-compose logs backend
   ```

3. Verify port is listening:
   ```bash
   netstat -ano | findstr :8001
   ```

### Frontend Can't Connect to Backend

1. Verify backend is running on 8001
2. Check frontend API URL in `AppContent.js`
3. Check browser console for CORS errors
4. Ensure both services are on the same network (if using Docker)

---

## Production Deployment

### Change Ports for Production

**docker-compose.yml:**
```yaml
backend:
  ports:
    - "8001:8001"  # Keep internal, expose via reverse proxy

frontend:
  ports:
    - "3001:3001"  # Keep internal, expose via reverse proxy
```

**Use Nginx/Apache as reverse proxy:**
- Frontend: example.com (port 80/443)
- Backend API: example.com/api (port 80/443)

---

## Environment Variables

### Backend
```bash
MODEL_PATH=/app/models/breast_cancer_model.keras
PYTHONUNBUFFERED=1
```

### Frontend
```bash
REACT_APP_API_BASE_URL=http://localhost:8001
PORT=3001
```

---

## Health Checks

### Frontend Health
```bash
curl http://localhost:3001
```

### Backend Health
```bash
curl http://localhost:8001/health
```

### API Documentation
```
http://localhost:8001/docs
```

---

## Quick Reference

| Task | Command |
|------|---------|
| Start all services | `docker-compose up --build` |
| Stop all services | `docker-compose down` |
| View logs | `docker-compose logs -f` |
| Restart backend | `docker-compose restart backend` |
| Rebuild backend | `docker-compose build --no-cache backend` |
| Access frontend | http://localhost:3001 |
| Access backend API | http://localhost:8001 |
| API documentation | http://localhost:8001/docs |
