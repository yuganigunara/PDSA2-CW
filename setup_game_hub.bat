@echo off
setlocal
cd /d "%~dp0\game-hub-react"
set "PY_EXE=%~dp0knight's tour Problem (Python)\.venv\Scripts\python.exe"

if exist "%PY_EXE%" goto py_ok
echo Python virtual environment not found at:
echo %PY_EXE%
echo Create the venv first, then run setup again.
exit /b 1
:py_ok

echo Installing backend dependencies...
cd /d backend
"%PY_EXE%" -m pip install -r requirements.txt

if errorlevel 1 (
  echo Backend dependency installation failed.
  exit /b 1
)

echo Installing frontend dependencies...
cd /d ..\frontend
npm install

if errorlevel 1 (
  echo Frontend dependency installation failed.
  exit /b 1
)

echo Setup complete. Run run_game_hub.bat to start the app.
endlocal
