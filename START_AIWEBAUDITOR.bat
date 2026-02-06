@echo off
title AI Web Auditor
echo ============================================
echo           AI WEB AUDITOR
echo ============================================
echo.

:: Check if running from correct directory
if not exist "backend\main.py" (
    echo ERROR: Run this from AIWebAuditor folder
    pause
    exit /b 1
)

:: Start Backend (FastAPI)
echo [1/2] Starting Backend (FastAPI - port 8001)...
cd backend
start "AIWebAuditor Backend" cmd /k "python main.py"
cd ..

:: Wait for backend to start
timeout /t 3 /nobreak > nul

:: Start Frontend (Next.js)
echo [2/2] Starting Frontend (Next.js - port 3001)...
cd frontend
start "AIWebAuditor Frontend" cmd /k "npm run dev"
cd ..

echo.
echo ============================================
echo   Services Starting:
echo   - Backend:  http://localhost:8001
echo   - Frontend: http://localhost:3001
echo ============================================
echo.
echo Press any key to open the app in browser...
pause > nul

start http://localhost:3001
