@echo off
echo Starting Vehicle Detection Dashboard...
echo.

echo Starting Flask Backend...
start "Flask Backend" cmd /k "cd /d %~dp0backend && .venv\Scripts\activate && python app.py"

echo Waiting 5 seconds for backend to start...
timeout /t 5 /nobreak >nul

echo Starting React Frontend...
start "React Frontend" cmd /k "cd /d %~dp0frontend && npm start"

echo.
echo Both servers are starting...
echo Backend: http://localhost:5000
echo Frontend: http://localhost:3000
echo.
pause
