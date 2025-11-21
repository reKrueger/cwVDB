@echo off
echo ========================================
echo cwVDB - Interactive Query Mode
echo ========================================
echo.
echo Available commands:
echo   search ^<query^>     - Semantic search
echo   find ^<symbol^>      - Find implementations
echo   usage ^<symbol^>     - Find usages
echo   file ^<path^>        - Get file overview
echo   quit               - Exit
echo.
pause

python start.py query --interactive

pause
