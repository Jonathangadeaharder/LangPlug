@echo off
echo Starting servers manually...

echo.
echo Starting Backend...
cd /d "e:\Users\Jonandrop\IdeaProjects\LangPlug\Backend"
start "Backend" cmd /k "python main.py"
timeout /t 5

echo.
echo Starting Frontend...
cd /d "e:\Users\Jonandrop\IdeaProjects\LangPlug\Frontend"  
start "Frontend" cmd /k "npm run dev"
timeout /t 10

echo.
echo Both servers should be starting...
echo Backend: http://127.0.0.1:8000
echo Frontend: http://localhost:3001 (or 3000)
echo.
echo Press any key to run E2E tests...
pause

echo.
echo Running simple E2E tests...
cd /d "e:\Users\Jonandrop\IdeaProjects\LangPlug\tests\e2e"
npm test simple-ui-tests.test.ts

echo.
echo Tests completed! Check server windows for any issues.
pause