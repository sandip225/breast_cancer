# 🚀 How to Run the Breast Cancer Detection Project

## Quick Start (Windows)

### Option 1: Use the Startup Script (Recommended)
Simply double-click or run:
```bash
start_project.bat
```

This will automatically:
- ✅ Start the backend server on port 8001
- ✅ Start the frontend server on port 3001
- ✅ Open both servers in separate terminal windows

### Option 2: Manual Start

#### Start Backend:
```bash
cd backend
.\venv\Scripts\activate
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8001
```

#### Start Frontend (in a new terminal):
```bash
cd frontend
npm start
```

## Access Points

- 🌐 **Web Application:** http://localhost:3001
- 🔧 **Backend API:** http://localhost:8001
- 📖 **API Documentation:** http://localhost:8001/docs

## First Time Setup

If you haven't installed dependencies:

### Backend Dependencies:
```bash
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### Frontend Dependencies:
```bash
cd frontend
npm install
```

## Using the Application

1. **Login/Signup** - Create an account or login
2. **Upload Image** - Drag and drop or browse for a mammogram image
3. **View Analysis** - See the AI analysis results with:
   - Heatmap visualizations
   - Risk assessment
   - Detailed clinical findings
4. **Fullscreen View** - Click the ⛶ icon to view images in fullscreen mode
5. **Download Report** - Generate and download a PDF report

## Testing the Fullscreen Fix

1. Upload and analyze a mammogram image
2. Go to "Visual Analysis" section
3. Click the fullscreen button (⛶) in the bottom-right corner
4. Modal should open with the image (not blank!)
5. Use arrow keys or dots to navigate between visualizations
6. Press F12 to open console and see debug logs

## Troubleshooting

### Port Already in Use
If you see "port already in use" error:
- Close other instances of the servers
- Or change the port in the startup script

### Module Not Found
If you get import errors:
```bash
cd backend
.\venv\Scripts\activate
pip install -r requirements.txt
```

### Frontend Won't Start
```bash
cd frontend
npm install
npm start
```

### Blank Fullscreen Modal
- Check browser console (F12) for error messages
- Look for the debug logs starting with 🖼️
- Ensure images are being loaded from the backend
- Try refreshing the page (Ctrl+F5)

## Stopping the Servers

Simply close the terminal windows that opened for the backend and frontend, or press `Ctrl+C` in each terminal.

## Notes

- Backend runs on port **8001**
- Frontend runs on port **3001**
- The frontend automatically detects localhost and uses the local backend
- For production deployment, set `REACT_APP_API_BASE_URL` environment variable

