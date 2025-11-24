@echo off
REM Generate documentation from VectorDB
REM Usage examples:
REM   generate_docs.bat --class CCwTsiModel
REM   generate_docs.bat --module tsi
REM   generate_docs.bat --find-undocumented

cd /d "%~dp0"

if not exist "env\Scripts\activate.bat" (
    echo Error: Virtual environment not found. Run setup.bat first.
    exit /b 1
)

call env\Scripts\activate.bat
python generate_docs.py %*
