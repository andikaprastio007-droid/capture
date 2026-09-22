@echo off
title Stalker - OSINT Investigation Tool
cd /d "%~dp0"

echo ========================================
echo   Stalker - OSINT Investigation Tool
echo ========================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Install Python 3.10+ from https://python.org
    pause
    exit /b 1
)
echo [OK] Python:
python --version 2>&1
echo.

:: Step 1: install base dependencies first
echo [SETUP] Installing base dependencies...
python -m pip install httpx click rich python-dotenv jinja2 googlesearch-python pyvis networkx phonenumbers --quiet
if errorlevel 1 (
    echo [ERROR] Failed to install base dependencies!
    pause
    exit /b 1
)
echo [OK] Base dependencies installed

:: Step 2: install maigret from local clone
echo [SETUP] Installing Maigret from local clone...
python -m pip install -e maigret\ --quiet
if errorlevel 1 (
    echo [ERROR] Failed to install Maigret from local clone.
    pause
    exit /b 1
)
echo [OK] Maigret installed

:: UTF-8 for Windows console
set PYTHONIOENCODING=utf-8

:: Create dirs
if not exist "output" mkdir "output"
if not exist "output\images" mkdir "output\images"

:: Create .env from example
if not exist ".env" (
    if exist ".env.example" copy .env.example .env >nul 2>&1
)

:: Launch menu
python -m stalker.menu

pause
