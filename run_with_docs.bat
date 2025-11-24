@echo off
REM ============================================
REM  cwVDB - Index and Generate Documentation
REM ============================================

cd /d "%~dp0"

if not exist "env\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Run setup.bat first.
    pause
    exit /b 1
)

call env\Scripts\activate.bat

echo.
echo ============================================
echo  cwVDB Indexer + Documentation Generator
echo ============================================
echo.
echo Options:
echo   1. Full reindex + generate docs
echo   2. Incremental update + generate docs
echo   3. Only generate docs (no indexing)
echo   4. Generate docs for specific module
echo   5. Exit
echo.

set /p choice="Select option (1-5): "

if "%choice%"=="1" (
    echo.
    echo Running full index with documentation...
    python indexer.py --initial --generate-docs --docs-limit 100
) else if "%choice%"=="2" (
    echo.
    echo Running incremental update with documentation...
    python indexer.py --incremental --generate-docs --docs-limit 50
) else if "%choice%"=="3" (
    echo.
    set /p limit="How many classes to document? (default 50): "
    if "%limit%"=="" set limit=50
    python indexer.py --generate-docs --docs-limit %limit%
) else if "%choice%"=="4" (
    echo.
    set /p module="Enter module name (e.g., tsi, fgm, ceo): "
    set /p limit="How many classes? (default 20): "
    if "%limit%"=="" set limit=20
    python generate_docs.py --module %module% --limit %limit%
) else if "%choice%"=="5" (
    exit /b 0
) else (
    echo Invalid option
)

echo.
echo ============================================
echo  Complete!
echo ============================================
echo.
echo Generated docs are in: knowledge\generated\
echo.

pause
