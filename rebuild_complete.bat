@echo off
REM ==============================================================================
REM cwVDB Complete Rebuild Script
REM Rebuilds entire VectorDB with hierarchical indexing and documentation
REM ==============================================================================

echo.
echo ================================================================================
echo cwVDB Complete Rebuild
echo ================================================================================
echo.
echo This script will:
echo   1. Delete existing VectorDB
echo   2. Run hierarchical indexing (may take several hours)
echo   3. Generate smart documentation
echo   4. Create knowledge base for token-efficient queries
echo.
echo Press Ctrl+C to cancel, or
pause

REM Check if already in virtual environment
if defined VIRTUAL_ENV (
    echo.
    echo [1/4] Virtual environment already active: %VIRTUAL_ENV%
    goto skip_activate
)

REM Try to activate virtual environment (try both common names)
echo.
echo [1/4] Activating virtual environment...

if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    goto skip_activate
)

if exist "env\Scripts\activate.bat" (
    call env\Scripts\activate.bat
    goto skip_activate
)

echo WARNING: No virtual environment found (venv or env)
echo Continuing without activation...

:skip_activate

REM Delete old VectorDB
echo.
echo [2/4] Cleaning old VectorDB...
if exist "vectordb" (
    rmdir /s /q vectordb
    echo Old VectorDB deleted
) else (
    echo No old VectorDB found
)

REM Delete old knowledge base
echo.
echo Cleaning old knowledge base...
if exist "knowledge" (
    rmdir /s /q knowledge
    echo Old knowledge base deleted
) else (
    echo No old knowledge base found
)

REM Run hierarchical indexing
echo.
echo [3/4] Starting hierarchical indexing...
echo This may take several hours depending on codebase size
echo Progress will be shown below...
echo.
python hierarchical_indexer.py
if errorlevel 1 (
    echo.
    echo ERROR: Hierarchical indexing failed!
    echo Check logs in ./logs/ for details
    pause
    exit /b 1
)

REM Run analysis and documentation generation
echo.
echo [4/4] Generating smart documentation...
echo.
python analyze_and_refine.py
if errorlevel 1 (
    echo.
    echo ERROR: Documentation generation failed!
    echo Check logs for details
    pause
    exit /b 1
)

REM Show final status
echo.
echo ================================================================================
echo Rebuild Complete!
echo ================================================================================
echo.
echo VectorDB Location: %CD%\vectordb
echo Knowledge Base: %CD%\knowledge
echo Logs: %CD%\logs
echo.
echo Next Steps:
echo   1. Test the system: test_hierarchical.bat
echo   2. Interactive mode: python hierarchical_query.py --interactive
echo   3. Query directly: python hierarchical_query.py --query "your question"
echo   4. Show knowledge base: python hierarchical_query.py --kb
echo.
echo Token Savings: 70-90%% compared to regular queries!
echo.
echo ================================================================================

pause
