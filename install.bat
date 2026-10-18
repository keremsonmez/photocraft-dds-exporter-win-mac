@echo off
title PhotoCraft NVIDIA DDS Exporter Installer
cd /d "%~dp0"
echo ===================================================
echo  PhotoCraft NVIDIA DDS Exporter Installer
echo ===================================================
echo.
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not found in system PATH.
    echo Please install Python 3.8 or newer from https://www.python.org/
    echo and make sure to check "Add Python to PATH" during setup.
    echo.
    pause
    exit /b 1
)

python installer\install.py
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Installation failed.
    pause
    exit /b %errorlevel%
) else (
    echo.
    pause
)
