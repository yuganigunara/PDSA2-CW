@echo off
setlocal
set "ROOT=%~dp0"
cd /d "%ROOT%"

where npm >nul 2>nul
if errorlevel 1 (
  echo npm was not found. Install Node.js LTS and reopen terminal.
  exit /b 1
)

set "PY_EXE=%ROOT%.venv\Scripts\python.exe"
if not exist "%PY_EXE%" (
  echo Creating workspace virtual environment at .venv ...
  where py >nul 2>nul
  if %errorlevel%==0 (
    py -3 -m venv "%ROOT%.venv"
  ) else (
    where python >nul 2>nul
    if errorlevel 1 (
      echo Python was not found. Install Python 3.10+ and add it to PATH.
      exit /b 1
    )
    python -m venv "%ROOT%.venv"
  )
)

if not exist "%PY_EXE%" (
  echo Failed to create or locate .venv Python executable.
  exit /b 1
)

echo Using Python: %PY_EXE%
"%PY_EXE%" -m pip install --upgrade pip
if errorlevel 1 (
  echo pip upgrade failed.
  exit /b 1
)

echo Installing backend dependencies...
cd /d "%ROOT%game-hub-react\backend"
"%PY_EXE%" -m pip install -r requirements.txt

if errorlevel 1 (
  echo Backend dependency installation failed.
  exit /b 1
)

echo Installing Snake dependencies...
cd /d "%ROOT%snake"
if exist requirements.txt (
  "%PY_EXE%" -m pip install -r requirements.txt
  if errorlevel 1 (
    echo Snake dependency installation failed.
    exit /b 1
  )
)

echo Installing Traffic Simulation dependencies...
cd /d "%ROOT%Traffic simulation Problem"
if exist requirements.txt (
  "%PY_EXE%" -m pip install -r requirements.txt
  if errorlevel 1 (
    echo Traffic Simulation dependency installation failed.
    exit /b 1
  )
)

echo Installing Knight's Tour package...
cd /d "%ROOT%knight's tour Problem (Python)"
if exist pyproject.toml (
  "%PY_EXE%" -m pip install -e .
  if errorlevel 1 (
    echo Knight's Tour installation failed.
    exit /b 1
  )
)

echo Installing frontend dependencies...
cd /d "%ROOT%game-hub-react\frontend"
npm install

if errorlevel 1 (
  echo Frontend dependency installation failed.
  exit /b 1
)

echo Installing Knight's Tour frontend dependencies...
cd /d "%ROOT%knight's tour Problem (Python)\frontend"
npm install

if errorlevel 1 (
  echo Knight's Tour frontend dependency installation failed.
  exit /b 1
)

echo Setup complete. Run run_game_hub.bat to start the app.
endlocal
