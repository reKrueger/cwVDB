@echo off
REM ==============================================================================
REM Quick Test Script for Hierarchical System
REM ==============================================================================

echo.
echo ================================================================================
echo cwVDB Hierarchical System Test
echo ================================================================================
echo.

REM Activate venv
call venv\Scripts\activate.bat

REM Test 1: Show knowledge base
echo [Test 1] Knowledge Base Summary
echo.
python hierarchical_query.py --kb
echo.
pause

REM Test 2: Level 0 search (ultra-fast, minimal tokens)
echo.
echo [Test 2] Level 0 Search (File Summaries)
echo.
python hierarchical_query.py --level 0 --query "main functions"
echo.
pause

REM Test 3: Level 1 search (file overviews)
echo.
echo [Test 3] Level 1 Search (File Overviews)
echo.
python hierarchical_query.py --level 1 --query "initialization"
echo.
pause

REM Test 4: Hierarchical search (progressive detail)
echo.
echo [Test 4] Hierarchical Search (All Levels)
echo.
python hierarchical_query.py --query "error handling"
echo.
pause

REM Test 5: Interactive mode
echo.
echo [Test 5] Interactive Mode
echo Try commands like: search, level, find, kb
echo.
python hierarchical_query.py --interactive

echo.
echo ================================================================================
echo Tests Complete!
echo ================================================================================
pause
