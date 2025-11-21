@echo off
REM Start cwVDB REST API
REM This script starts the REST API server for querying the vector database

echo ================================================================================
echo cwVDB REST API Startup
echo ================================================================================
echo.

cd /d "%~dp0"

REM Check if virtual environment exists (try both env and venv)
if exist "env\Scripts\activate.bat" (
    call env\Scripts\activate.bat
) else if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo WARNING: Virtual environment not found!
    echo Trying to run without venv activation...
    echo.
)

REM Check if vectordb exists
if not exist "vectordb" (
    echo WARNING: Vector database not found!
    echo Please run: run_test_indexing.bat
    echo.
    echo Continuing anyway - API will start but queries may fail...
    echo.
)

REM Start API server
echo Starting REST API on http://localhost:8000
echo Press Ctrl+C to stop the server
echo.
echo Endpoints:
echo   GET  /health          - Health check
echo   GET  /statistics      - Database statistics
echo   POST /search          - Search for code
echo   POST /find            - Find implementations
echo   POST /usage           - Find usages
echo   POST /file            - File overview
echo   POST /similar         - Find similar code
echo.
echo ================================================================================
echo.

python start.py api --port 8000

pause
