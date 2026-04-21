#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_DIR="$ROOT/.run"
LOG_DIR="$RUN_DIR/logs"
PID_DIR="$RUN_DIR/pids"
mkdir -p "$LOG_DIR" "$PID_DIR"

if [[ -x "$ROOT/.venv/bin/python" ]]; then
  PY_EXE="$ROOT/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PY_EXE="python3"
else
  echo "Python not found. Install Python 3 (or create .venv) and retry."
  exit 1
fi

echo "Using Python: $PY_EXE"

echo "Cleaning known ports..."
PORTS=(5000 5001 5174 5176 5180 5187 5190 8001 8002 8003 8006)
for port in "${PORTS[@]}"; do
  pids="$(lsof -ti tcp:${port} -sTCP:LISTEN || true)"
  if [[ -n "$pids" ]]; then
    echo "$pids" | xargs -n1 kill -9 2>/dev/null || true
  fi
done

launch() {
  local name="$1"
  local cwd="$2"
  local cmd="$3"
  local log_file="$LOG_DIR/${name}.log"
  local pid_file="$PID_DIR/${name}.pid"

  nohup bash -lc "cd \"$cwd\" && $cmd" >"$log_file" 2>&1 &
  echo $! >"$pid_file"
  echo "Started $name (pid $(cat "$pid_file"))"
}

echo "Starting Game Hub backend (8002) and frontend (5180)..."
launch "game_hub_api" "$ROOT/game-hub-react/backend" "$PY_EXE -m uvicorn app.main:app --host 127.0.0.1 --port 8002"
launch "game_hub_frontend" "$ROOT/game-hub-react/frontend" "npm run dev -- --host localhost --port 5180 --strictPort"

echo "Starting Snake backend (8001) and frontend (5176)..."
launch "snake_api" "$ROOT/snake" "$PY_EXE -m uvicorn snake_ladder.api:app --host 127.0.0.1 --port 8001"
launch "snake_frontend" "$ROOT/snake/frontend" "npm run dev -- --host localhost --port 5176 --strictPort"

echo "Starting Knight Tour backend (5001) and frontend (5174)..."
launch "knight_api" "$ROOT/knight's tour Problem (Python)" "$PY_EXE run_api.py"
launch "knight_frontend" "$ROOT/knight's tour Problem (Python)/frontend" "npm run dev -- --host localhost --port 5174 --strictPort"

echo "Starting Traffic Simulation (5000)..."
launch "traffic_app" "$ROOT/Traffic simulation Problem" "$PY_EXE run.py"

echo "Starting Sixteen Queens backend (8003) and frontend (5190)..."
launch "sixteen_api" "$ROOT/sixteen queens/backend" "$PY_EXE -m uvicorn main:app --host 127.0.0.1 --port 8003"
launch "sixteen_frontend" "$ROOT/sixteen queens/frontend" "npm run dev -- --host localhost --port 5190 --strictPort"

echo "Starting Minimum Cost backend (8006) and frontend (5187)..."
launch "min_cost_api" "$ROOT/minimum,_cost_problem/server" "$PY_EXE -m uvicorn app:app --host 127.0.0.1 --port 8006"
launch "min_cost_frontend" "$ROOT/minimum,_cost_problem/client" "npm run dev -- --host localhost --port 5187 --strictPort"

echo
echo "All launch commands sent."
echo "Game Hub:      http://localhost:5180/"
echo "Snake:         http://localhost:5176/"
echo "Knight Tour:   http://localhost:5174/"
echo "Traffic:       http://127.0.0.1:5000/"
echo "SixteenQueens: http://localhost:5190/"
echo "Minimum Cost:  http://localhost:5187/"
echo

if command -v open >/dev/null 2>&1; then
  open "http://localhost:5180/" || true
fi
