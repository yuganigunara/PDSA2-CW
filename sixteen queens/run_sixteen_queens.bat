@echo off
setlocal
set "ROOT=%~dp0"
set "PY_EXE=%ROOT%.venv\Scripts\python.exe"
set "BACKEND_DIR=%ROOT%sixteen queens\backend"
set "FRONTEND_DIR=%ROOT%sixteen queens\frontend"

if not exist "%PY_EXE%" (
  echo Python virtual environment not found at:
  echo %PY_EXE%
  exit /b 1
)

netstat -ano | findstr /R ":8003 .*LISTENING" >nul
if errorlevel 1 (
  start "Sixteen Queens API" cmd /k "cd /d \"%BACKEND_DIR%\" && \"%PY_EXE%\" -m uvicorn main:app --host 127.0.0.1 --port 8003"
)

netstat -ano | findstr /R ":5190 .*LISTENING" >nul
if errorlevel 1 (
  start "Sixteen Queens Frontend" cmd /k "cd /d \"%FRONTEND_DIR%\" && npm run dev -- --host localhost --port 5190 --strictPort"
)

endlocal
