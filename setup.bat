@echo off
REM cwVDB Setup Script for Windows
REM Installs dependencies and prepares the environment

echo ========================================
echo cwVDB Setup Script
echo ========================================
echo.

REM Check Python
echo [1/5] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Please install Python 3.8+ from python.org
    pause
    exit /b 1
)
python --version
echo Python OK
echo.

REM Check pip
echo [2/5] Checking pip...
pip --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: pip not found!
    pause
    exit /b 1
)
echo pip OK
echo.

REM Create virtual environment (optional but recommended)
echo [3/5] Create virtual environment? (recommended)
set /p CREATE_VENV="Create venv? (y/n): "
if /i "%CREATE_VENV%"=="y" (
    echo Creating virtual environment...
    python -m venv venv
    echo.
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
    echo Virtual environment activated!
    echo.
)

REM Install dependencies
echo [4/5] Installing dependencies...
echo This may take a few minutes...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies!
    pause
    exit /b 1
)
echo.
echo Dependencies installed successfully!
echo.

REM Verify source path
echo [5/5] Verifying source path...
if exist "C:\source\cadlib\v_33.0" (
    echo Source path found: C:\source\cadlib\v_33.0
) else (
    echo WARNING: Source path not found: C:\source\cadlib\v_33.0
    echo Please update config.json with correct path
)
echo.

echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo   1. Update config.json if needed (source path, etc.)
echo   2. Run initial indexing:
echo      python indexer.py --initial
echo   3. Query the database:
echo      python query.py --interactive
echo.
echo Note: Initial indexing of 60GB may take 4-8 hours
echo       You can resume from checkpoints if interrupted
echo.
pause
