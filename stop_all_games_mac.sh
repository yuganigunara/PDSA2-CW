#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_DIR="$ROOT/.run/pids"

echo "Stopping all game and hub services..."

if [[ -d "$PID_DIR" ]]; then
  for pid_file in "$PID_DIR"/*.pid; do
    [[ -f "$pid_file" ]] || continue
    pid="$(cat "$pid_file" 2>/dev/null || true)"
    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
      kill -9 "$pid" 2>/dev/null || true
      echo "Killed PID $pid ($(basename "$pid_file" .pid))"
    fi
    rm -f "$pid_file"
  done
fi

PORTS=(5000 5001 5174 5176 5180 5187 5190 8001 8002 8003 8006)
for port in "${PORTS[@]}"; do
  pids="$(lsof -ti tcp:${port} -sTCP:LISTEN || true)"
  if [[ -n "$pids" ]]; then
    echo "$pids" | xargs -n1 kill -9 2>/dev/null || true
  fi
done

echo
echo "Verifying ports are closed..."
for port in "${PORTS[@]}"; do
  if lsof -i tcp:${port} -sTCP:LISTEN >/dev/null 2>&1; then
    echo "PORT ${port}: True"
  else
    echo "PORT ${port}: False"
  fi
done

echo
echo "Done."
