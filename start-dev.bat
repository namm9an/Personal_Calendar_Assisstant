@echo off
echo Starting Personal Calendar Assistant in development mode...

REM Start backend in a new window
start cmd /k "python run.py"

REM Wait a bit for backend to initialize
timeout /t 5 /nobreak

REM Start frontend in a new window
start cmd /k "cd frontend && npm run dev"

echo Both servers started!
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000 