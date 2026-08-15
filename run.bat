@echo off
chcp 65001 >nul
title Classroom Quality Monitoring System Launcher

echo ============================================================
echo   Classroom Quality Monitoring System
echo   Starting Backend (FastAPI + YOLOv8 + Qwen2.5-VL) and Frontend
echo ============================================================
echo.

set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

:: Check root directory
if not exist "backend\main.py" (
    echo [ERROR] backend\main.py not found! Please run from project root.
    pause
    exit /b 1
)

:: Check Python Virtual Environment
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Python virtual environment not found at 'venv\'.
    echo Please create it using: python -m venv venv
    pause
    exit /b 1
)

:: Check Frontend Node Modules
if not exist "frontend\node_modules" (
    echo [INFO] frontend\node_modules not found. Installing node dependencies...
    cd /d "%PROJECT_DIR%frontend"
    call npm install
    cd /d "%PROJECT_DIR%"
)

echo [1/3] Starting Ollama Model Server...
start "Ollama Server" cmd /k "ollama serve"
ping -n 3 127.0.0.1 >nul

echo [2/3] Starting FastAPI Backend on http://localhost:8000 ...
start "FastAPI Backend" cmd /k "cd /d "%PROJECT_DIR%" && call venv\Scripts\activate.bat && uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000"
ping -n 3 127.0.0.1 >nul

echo [3/3] Starting React Frontend on http://localhost:5173 ...
start "React Frontend" cmd /k "cd /d "%PROJECT_DIR%frontend" && npm run dev"

echo.
echo ============================================================
echo   ALL SERVICES LAUNCHED!
echo   - Frontend App  : http://localhost:5173
echo   - Backend Docs  : http://localhost:8000/docs
echo   - Ollama API    : http://localhost:11434
echo ============================================================
echo.
pause
