@echo off
setlocal
set "ROOT=%~dp0"
cd /d "%ROOT%game-hub-react"
set "PY_EXE=%ROOT%.venv\Scripts\python.exe"
if exist "%PY_EXE%" goto py_ok

set "PY_EXE=%ROOT%knight's tour Problem (Python)\.venv\Scripts\python.exe"
if exist "%PY_EXE%" goto py_ok

where python >nul 2>nul
if %errorlevel%==0 (
	set "PY_EXE=python"
	goto py_ok
)

echo Python was not found.
echo Run setup_game_hub.bat after installing Python and Node.js.
pause
exit /b 1

:py_ok
echo Using Python: %PY_EXE%

start "Game Hub API" cmd /k "cd /d backend && \"%PY_EXE%\" -m uvicorn app.main:app --host 127.0.0.1 --port 8002 --reload"
start "Game Hub Frontend" cmd /k "cd /d frontend && npm run dev -- --host localhost --port 5180"

timeout /t 3 >nul
start "" http://localhost:5180
endlocal