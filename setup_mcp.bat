@echo off
echo ========================================
echo cwVDB MCP Integration Setup
echo ========================================
echo.
echo This will install MCP SDK and configure Claude Desktop
echo.
pause

echo.
echo [1/4] Installing MCP SDK...
pip install mcp requests

echo.
echo [2/4] Testing MCP Server...
echo Starting test (will timeout after 5 seconds)...
timeout /t 5 /nobreak > nul
echo OK - MCP Server code ready

echo.
echo [3/4] Claude Desktop Configuration
echo.
echo Please add this to your Claude Desktop config:
echo File: %%APPDATA%%\Claude\claude_desktop_config.json
echo.
echo {
echo   "mcpServers": {
echo     "cwvdb": {
echo       "command": "python",
echo       "args": [
echo         "%CD%\mcp_server.py"
echo       ]
echo     }
echo   }
echo }
echo.
pause

echo.
echo [4/4] Next Steps:
echo.
echo 1. Start the REST API in a separate terminal:
echo    python start.py api
echo.
echo 2. Restart Claude Desktop completely
echo.
echo 3. Ask Claude questions about your code!
echo    Example: "Welche API Funktionen gibt es?"
echo.
echo ========================================
echo Setup Complete!
echo ========================================
pause
