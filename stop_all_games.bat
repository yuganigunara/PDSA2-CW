@echo off
setlocal

set "ROOT=%~dp0"
cd /d "%ROOT%"

echo Stopping all game and hub services...

for %%P in (5000 5001 5174 5176 5180 5187 5190 8001 8002 8003 8006) do (
  for /f "tokens=5" %%A in ('netstat -ano ^| findstr /R /C:":%%P .*LISTENING"') do (
    echo Killing PID %%A on port %%P
    taskkill /PID %%A /F >nul 2>nul
  )
)

echo.
echo Verifying ports are closed...
powershell -NoProfile -Command "$ports = 5000,5001,5174,5176,5180,5187,5190,8001,8002,8003,8006; foreach ($p in $ports) { $ok = (Test-NetConnection 127.0.0.1 -Port $p -WarningAction SilentlyContinue).TcpTestSucceeded; Write-Host ('PORT {0}: {1}' -f $p, $ok) }"

echo.
echo Done. You can now relaunch with run_all_games.bat
endlocal
