@echo off
echo ========================================
echo cwVDB - Initial Indexing
echo ========================================
echo.
echo Source: common module
echo This will OVERWRITE existing database
echo.
pause

echo.
echo Starting indexing...
echo.

python indexer.py --initial

echo.
echo ========================================
echo Indexing Complete!
echo ========================================
pause
