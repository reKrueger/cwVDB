@echo off
REM Start cwVDB REST API
REM This script starts the REST API server for querying the vector database

echo ================================================================================
echo cwVDB REST API Startup
echo ================================================================================
echo.

cd /d "%~dp0"

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Please run setup.bat first.
    echo.
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Check if vectordb exists
if not exist "vectordb" (
    echo WARNING: Vector database not found!
    echo Please run: python indexer.py --initial
    echo.
    pause
    exit /b 1
)

REM Start API server
echo Starting REST API on http://localhost:8000
echo Press Ctrl+C to stop the server
echo.
echo Endpoints:
echo   GET  /health          - Health check
echo   GET  /stats           - Database statistics
echo   POST /search          - Search for code
echo   POST /find            - Find implementations
echo   POST /usage           - Find usages
echo   POST /file            - File overview
echo   POST /similar         - Find similar code
echo.
echo ================================================================================
echo.

python query_api.py --port 8000

pause
