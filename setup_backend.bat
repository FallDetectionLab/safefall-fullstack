@echo off
REM SafeFall Backend Quick Setup Script for Windows
REM ================================================

echo.
echo ========================================
echo   SafeFall Backend Setup (Windows)
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/
    pause
    exit /b 1
)

echo [1/7] Checking Python version...
python --version

echo.
echo [2/7] Creating virtual environment...
cd Back
python -m venv venv

echo.
echo [3/7] Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo [4/7] Upgrading pip...
python -m pip install --upgrade pip

echo.
echo [5/7] Installing dependencies...
pip install -r requirements.txt

echo.
echo [6/7] Creating necessary directories...
if not exist "videos" mkdir videos
if not exist "instance" mkdir instance

echo.
echo [7/7] Initializing default user...
python init_default_user.py

echo.
echo ========================================
echo   Setup Complete!
echo ========================================
echo.
echo Default User Created:
echo   ID: admin
echo   Password: admin123
echo.
echo Next Steps:
echo   1. Keep this window open (virtual environment is active)
echo   2. Run: python app.py
echo   3. Open browser: http://localhost:5000/health
echo.
echo ========================================

pause
