@echo off
setlocal enabledelayedexpansion
title Classroom Quality Monitoring System Setup

echo ====================================================================
echo   Classroom Quality Monitoring System - Environment Setup
echo ====================================================================
echo.

set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

rem ---------------------------------------------------------------------
rem 0. Verification of Root Directory
rem ---------------------------------------------------------------------
if not exist "backend\main.py" (
    echo [ERROR] backend\main.py not found!
    echo Please run setup.bat from the root directory of the project.
    pause
    exit /b 1
)

rem ---------------------------------------------------------------------
rem 1. Check Prerequisites: Python, Node.js, Ollama
rem ---------------------------------------------------------------------
echo [1/5] Checking system prerequisites...

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in your system PATH!
    echo Please install Python 3.10 or 3.11 from https://www.python.org/
    echo NOTE: Make sure to check Add python.exe to PATH during installation.
    pause
    exit /b 1
)
echo  - Python: OK

where npm >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Node.js or npm is not installed or not in PATH.
    echo Please install Node.js v18 or newer from https://nodejs.org/
) else (
    echo  - Node.js / npm: OK
)

where ollama >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Ollama is not installed or not in PATH.
    echo Install Ollama from https://ollama.com/ to run the AI vision model.
) else (
    echo  - Ollama: OK
)
echo.

rem ---------------------------------------------------------------------
rem 2. Setup Python Virtual Environment venv in Project Root
rem ---------------------------------------------------------------------
echo [2/5] Setting up Python Virtual Environment venv...
if not exist "venv\Scripts\activate.bat" (
    echo  - Creating virtual environment venv in project root...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
) else (
    echo  - Virtual environment venv already exists.
)

echo  - Activating virtual environment...
call venv\Scripts\activate.bat

echo  - Upgrading pip...
python -m pip install --upgrade pip

echo  - Installing backend dependencies from backend\requirements.txt...
pip install -r backend\requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install backend dependencies.
    pause
    exit /b 1
)
echo  - Backend dependencies installed successfully!
echo.

rem ---------------------------------------------------------------------
rem 3. Setup Frontend Dependencies
rem ---------------------------------------------------------------------
echo [3/5] Setting up Frontend dependencies...
if exist "frontend\package.json" (
    where npm >nul 2>&1
    if not errorlevel 1 (
        cd /d "%PROJECT_DIR%frontend"
        echo  - Running npm install in frontend directory...
        call npm install
        cd /d "%PROJECT_DIR%"
        echo  - Frontend dependencies installed successfully!
    ) else (
        echo  - npm not found, skipping frontend npm install.
    )
)
echo.

rem ---------------------------------------------------------------------
rem 4. Setup Ollama Vision Model
rem ---------------------------------------------------------------------
echo [4/5] Ollama Vision Model Setup...
where ollama >nul 2>&1
if not errorlevel 1 (
    echo.
    echo Base model required: qwen2.5vl:7b
    set /p PULL_MODEL="Do you want to download and configure Ollama model now? [Y/N]: "
    if /i "!PULL_MODEL!"=="Y" (
        echo  - Pulling base model qwen2.5vl:7b ...
        ollama pull qwen2.5vl:7b
        echo  - Creating customized classroom-qwen model from Modelfile...
        ollama create classroom-qwen -f backend\fine_tuning\Modelfile
        echo  - Model setup complete!
    ) else (
        echo  - Skipped. You can configure it later with:
        echo      ollama pull qwen2.5vl:7b
        echo      ollama create classroom-qwen -f backend\fine_tuning\Modelfile
    )
) else (
    echo  - Ollama is not installed. Install it from https://ollama.com/
)
echo.

rem ---------------------------------------------------------------------
rem 5. Completed
rem ---------------------------------------------------------------------
echo [5/5] Setup Summary
echo ====================================================================
echo   SUCCESS! Environment setup is complete.
echo.
echo   To launch the entire application:
echo     Run: run.bat
echo ====================================================================
echo.
pause
