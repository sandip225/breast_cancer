@echo off
REM Automated GitHub Push Script
REM Run this to push code to GitHub

echo.
echo ========================================
echo  GitHub Push Script
echo ========================================
echo.

REM Get GitHub username
set /p GITHUB_USERNAME="Enter your GitHub username: "

echo.
echo [1/3] Initializing Git repositories...
echo.

REM Backend repository
echo Setting up Backend repository...
cd backend
if not exist .git (
    git init
    git branch -M main
)

REM Add all files
git add .
git commit -m "Backend deployment for Render"

echo.
echo Backend repository URL should be:
echo https://github.com/%GITHUB_USERNAME%/breast-cancer-backend
echo.
set /p BACKEND_REPO="Enter backend repository URL (or press Enter to use above): "
if "%BACKEND_REPO%"=="" set BACKEND_REPO=https://github.com/%GITHUB_USERNAME%/breast-cancer-backend

echo Adding remote...
git remote remove origin 2>nul
git remote add origin %BACKEND_REPO%

echo.
echo [2/3] Pushing Backend to GitHub...
echo.
git push -u origin main

cd ..

REM Frontend repository
echo.
echo Setting up Frontend repository...
cd frontend
if not exist .git (
    git init
    git branch -M main
)

REM Add all files
git add .
git commit -m "Frontend deployment for Render"

echo.
echo Frontend repository URL should be:
echo https://github.com/%GITHUB_USERNAME%/breast-cancer-frontend
echo.
set /p FRONTEND_REPO="Enter frontend repository URL (or press Enter to use above): "
if "%FRONTEND_REPO%"=="" set FRONTEND_REPO=https://github.com/%GITHUB_USERNAME%/breast-cancer-frontend

echo Adding remote...
git remote remove origin 2>nul
git remote add origin %FRONTEND_REPO%

echo.
echo [3/3] Pushing Frontend to GitHub...
echo.
git push -u origin main

cd ..

echo.
echo ========================================
echo  GitHub Push Complete!
echo ========================================
echo.
echo Next Steps:
echo 1. Go to Render.com dashboard
echo 2. Create Web Service for backend
echo 3. Create Static Site for frontend
echo 4. Add environment variables (see RENDER_DEPLOY_HINDI.md)
echo.
pause

