@echo off
setlocal
cd /d "%~dp0\game-hub-react"
set "PY_EXE=%~dp0knight's tour Problem (Python)\.venv\Scripts\python.exe"

if exist "%PY_EXE%" goto py_ok
echo Python virtual environment not found at:
echo %PY_EXE%
pause
exit /b 1
:py_ok

start "Game Hub API" cmd /k "cd /d backend && \"%PY_EXE%\" -m uvicorn app.main:app --host 127.0.0.1 --port 8002 --reload"
start "Game Hub Frontend" cmd /k "cd /d frontend && npm run dev -- --host localhost --port 5180"

timeout /t 3 >nul
start "" http://localhost:5180
endlocal