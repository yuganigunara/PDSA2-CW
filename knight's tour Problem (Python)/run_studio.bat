@echo off
setlocal
cd /d "%~dp0"

set "PY_EXE=%~1"
if "%PY_EXE%"=="" set "PY_EXE=%~dp0.venv\Scripts\python.exe"
if not exist "%PY_EXE%" set "PY_EXE=python"

start "Knight Tour API" cmd /k "cd /d ""%~dp0"" && ""%PY_EXE%"" run_api.py"
start "Knight Tour Studio" cmd /k "cd /d ""%~dp0frontend"" && npm run dev -- --host localhost --port 5174 --strictPort"

timeout /t 3 >nul
start "" http://127.0.0.1:5174/
endlocal
