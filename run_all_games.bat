@echo off
setlocal

set "ROOT=%~dp0"
cd /d "%ROOT%"

set "PY_EXE=%ROOT%.venv\Scripts\python.exe"
if exist "%PY_EXE%" goto py_ok

where python >nul 2>nul
if %errorlevel%==0 (
  set "PY_EXE=python"
  goto py_ok
)

echo Python was not found.
echo Install Python and create .venv, then rerun this script.
exit /b 1

:py_ok
echo Using Python: %PY_EXE%

echo.
echo Cleaning known ports...
for %%P in (5000 5001 5174 5176 5180 5187 5190 8001 8002 8003 8006) do (
  for /f "tokens=5" %%A in ('netstat -ano ^| findstr /R /C:":%%P .*LISTENING"') do (
    taskkill /PID %%A /F >nul 2>nul
  )
)

echo.
echo Starting Game Hub backend (8002) and frontend (5180)...
start "Game Hub API" cmd /k "cd /d "%ROOT%game-hub-react\backend" && "%PY_EXE%" -m uvicorn app.main:app --host 127.0.0.1 --port 8002"
start "Game Hub Frontend" cmd /k "cd /d "%ROOT%game-hub-react\frontend" && npm.cmd run dev -- --host localhost --port 5180 --strictPort"

echo Starting Snake backend (8001) and frontend (5176)...
start "Snake API" cmd /k "cd /d "%ROOT%snake" && "%PY_EXE%" -m uvicorn snake_ladder.api:app --host 127.0.0.1 --port 8001"
start "Snake Frontend" cmd /k "cd /d "%ROOT%snake\frontend" && npm.cmd run dev -- --host localhost --port 5176 --strictPort"

echo Starting Knight Tour backend (5001) and frontend (5174)...
start "Knight API" cmd /k "cd /d "%ROOT%knight's tour Problem (Python)" && "%PY_EXE%" run_api.py"
start "Knight Frontend" cmd /k "cd /d "%ROOT%knight's tour Problem (Python)\frontend" && npm.cmd run dev -- --host localhost --port 5174 --strictPort"

echo Starting Traffic Simulation (5000)...
start "Traffic Simulation" cmd /k "cd /d "%ROOT%Traffic simulation Problem" && "%PY_EXE%" run.py"

echo Starting Sixteen Queens backend (8003) and frontend (5190)...
start "Sixteen Queens API" cmd /k "cd /d "%ROOT%sixteen queens\backend" && "%PY_EXE%" -m uvicorn main:app --host 127.0.0.1 --port 8003"
start "Sixteen Queens Frontend" cmd /k "cd /d "%ROOT%sixteen queens\frontend" && npm.cmd run dev -- --host localhost --port 5190 --strictPort"

echo Starting Minimum Cost backend (8006) and frontend (5187)...
start "Minimum Cost API" cmd /k "cd /d "%ROOT%minimum,_cost_problem\server" && "%PY_EXE%" -m uvicorn app:app --host 127.0.0.1 --port 8006"
start "Minimum Cost Frontend" cmd /k "cd /d "%ROOT%minimum,_cost_problem\client" && npm.cmd run dev -- --host localhost --port 5187 --strictPort"

echo.
echo All launch commands sent.
echo Game Hub: http://localhost:5180/
echo Snake: http://localhost:5176/
echo Knight Tour: http://localhost:5174/
echo Traffic: http://127.0.0.1:5000/
echo Sixteen Queens: http://localhost:5190/
echo Minimum Cost: http://localhost:5187/
echo.
echo Note: Keep opened terminal windows running.

start "" http://localhost:5180/

endlocal
