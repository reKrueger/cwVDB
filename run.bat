@echo off
echo Starting cwVDB API in background...
start "cwVDB API" /MIN cmd /c "env\Scripts\activate && python start.py api"
echo API starting on http://127.0.0.1:8000
echo.
echo Done! Now restart Claude Desktop.
echo The cwVDB API window runs minimized in the taskbar.
pause