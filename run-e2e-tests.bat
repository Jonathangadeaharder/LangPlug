@echo off
setlocal

echo ====================================
echo Starting LangPlug E2E Test Suite
echo ====================================

:: Set error handling
set "error_occurred=false"

:: Trap Ctrl+C to cleanup
if "%1"=="cleanup" goto cleanup

:: Main execution starts here
goto main

:: Function to cleanup processes
:cleanup
echo.
echo Cleaning up processes...
taskkill /f /im node.exe >nul 2>&1
taskkill /f /im python.exe >nul 2>&1
timeout /t 2 >nul
goto :eof

:main

echo.
echo [1/4] Starting Backend Server...
echo ====================================
cd /d "e:\Users\Jonandrop\IdeaProjects\LangPlug\Backend"
start "LangPlug Backend" cmd /c "python main.py"

echo Waiting for backend to initialize...
timeout /t 8

echo.
echo [2/4] Starting Frontend Server...
echo ====================================
cd /d "e:\Users\Jonandrop\IdeaProjects\LangPlug\Frontend"
start "LangPlug Frontend" cmd /c "npm run dev && pause"

echo Waiting for frontend to initialize...
timeout /t 15

echo.
echo [3/4] Running Integration Tests First...
echo ====================================
echo Testing backend server startup...
cd /d "e:\Users\Jonandrop\IdeaProjects\LangPlug\Backend"
python -m pytest tests/integration/test_server_integration.py::TestBackendIntegration::test_server_starts_and_serves_docs -v --tb=short
if %errorlevel% neq 0 (
    echo ERROR: Backend integration test failed!
    goto cleanup_and_exit
)
echo Backend integration test passed!

echo.
echo Testing server health...
cd /d "e:\Users\Jonandrop\IdeaProjects\LangPlug"
python health_check.py --wait
if %errorlevel% neq 0 (
    echo ERROR: Server health check failed!
    goto cleanup_and_exit
)

echo.
echo [4/4] Running E2E Tests...
echo ====================================
echo ====================================
cd /d "e:\Users\Jonandrop\IdeaProjects\LangPlug\tests\e2e"
call npm test

:: Check if tests passed
if %errorlevel% neq 0 (
    echo.
    echo ====================================
    echo E2E TESTS FAILED!
    echo ====================================
    set "error_occurred=true"
) else (
    echo.
    echo ====================================
    echo E2E TESTS PASSED!
    echo ====================================
)

:cleanup_and_exit
echo.
echo [5/5] Cleaning Up...
echo ====================================
call "%~dp0run-e2e-tests.bat" cleanup

if "%error_occurred%"=="true" (
    echo.
    echo Test execution completed with errors.
    pause
    exit /b 1
) else (
    echo.
    echo Test execution completed successfully!
    pause
    exit /b 0
)