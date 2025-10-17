@echo off
REM SafeFall Frontend Quick Setup Script for Windows
REM =================================================

echo.
echo ========================================
echo   SafeFall Frontend Setup (Windows)
echo ========================================
echo.

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js is not installed or not in PATH
    echo Please install Node.js 18+ from https://nodejs.org/
    pause
    exit /b 1
)

echo [1/3] Checking Node.js version...
node --version
npm --version

echo.
echo [2/3] Installing dependencies...
cd Front
npm install

echo.
echo [3/3] Setup complete!

echo.
echo ========================================
echo   Setup Complete!
echo ========================================
echo.
echo Next Steps:
echo   1. Run: npm run dev
echo   2. Open browser: http://localhost:5173
echo.
echo ========================================

pause
