from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


ROOT_DIR = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT_DIR / "game_hub_config.json"

DEFAULT_GAMES = [
    {
        "name": "Snake and Ladder",
        "cwd": "snake",
        "command": ["{python}", "main.py"],
        "enabled": True,
        "needs_src_path": False,
    },
    {
        "name": "Knight's Tour Studio",
        "cwd": "knight's tour Problem (Python)",
        "command": ["{python}", "run_studio.py"],
        "enabled": True,
        "needs_src_path": False,
    },
    {
        "name": "Traffic simulation Problem",
        "cwd": "Traffic simulation Problem",
        "command": ["{python}", "run.py"],
        "enabled": True,
        "needs_src_path": False,
    },
    {
        "name": "Game Slot 4",
        "cwd": "",
        "command": [],
        "enabled": False,
        "needs_src_path": False,
    },
    {
        "name": "Game Slot 5",
        "cwd": "",
        "command": [],
        "enabled": False,
        "needs_src_path": False,
    },
]


class GameConfig(BaseModel):
    name: str = Field(min_length=1)
    cwd: str
    command: list[str]
    enabled: bool = True
    needs_src_path: bool = False


app = FastAPI(title="Game Hub API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _read_config() -> list[dict[str, Any]]:
    if not CONFIG_PATH.exists():
        raise HTTPException(status_code=404, detail="game_hub_config.json not found")
    return __import__("json").loads(CONFIG_PATH.read_text(encoding="utf-8"))


def _normalized_games(data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for index in range(5):
        fallback = dict(DEFAULT_GAMES[index])
        source = data[index] if index < len(data) and isinstance(data[index], dict) else {}
        fallback.update(source)
        normalized.append(fallback)
    return normalized


def _write_config(data: list[dict[str, Any]]) -> None:
    CONFIG_PATH.write_text(__import__("json").dumps(data, indent=2), encoding="utf-8")


def _get_traffic_simulation_logs() -> dict[str, Any]:
    """Get logs from Traffic Simulation database"""
    db_path = ROOT_DIR / "Traffic simulation Problem" / "traffic_game.db"
    
    if not db_path.exists():
        return {"error": "Database not found", "rounds": [], "wins": []}
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get recent rounds
        rounds = []
        for row in cursor.execute("SELECT * FROM rounds ORDER BY created_at DESC LIMIT 5").fetchall():
            rounds.append(dict(row))
        
        # Get leaderboard
        wins = []
        for row in cursor.execute("""
            SELECT player_name, COUNT(*) as wins_count, MAX(created_at) as last_play
            FROM wins
            GROUP BY player_name
            ORDER BY wins_count DESC
            LIMIT 10
        """).fetchall():
            wins.append(dict(row))
        
        conn.close()
        return {"rounds": rounds, "wins": wins}
    except Exception as e:
        return {"error": str(e), "rounds": [], "wins": []}


def _get_knights_tour_logs() -> dict[str, Any]:
    """Get logs from Knight's Tour database"""
    db_path = ROOT_DIR / "knight's tour Problem (Python)" / ".knights_tour.db"
    
    if not db_path.exists():
        return {"error": "Database not found", "games": [], "winners": []}
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get recent games
        games = []
        for row in cursor.execute("SELECT * FROM games ORDER BY created_at DESC LIMIT 5").fetchall():
            games.append(dict(row))
        
        # Get winners
        winners = []
        for row in cursor.execute("""
            SELECT player_name, COUNT(*) as wins_count, MAX(created_at) as last_win
            FROM winners
            GROUP BY player_name
            ORDER BY wins_count DESC
            LIMIT 10
        """).fetchall():
            winners.append(dict(row))
        
        conn.close()
        return {"games": games, "winners": winners}
    except Exception as e:
        return {"error": str(e), "games": [], "winners": []}


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/logs")
def get_game_logs() -> dict[str, Any]:
    """Get game logs from all games"""
    return {
        "traffic_simulation": _get_traffic_simulation_logs(),
        "knights_tour": _get_knights_tour_logs(),
        "timestamp": __import__("datetime").datetime.now().isoformat(),
    }


@app.get("/api/games")
def list_games() -> dict[str, Any]:
    games = _normalized_games(_read_config())
    return {"games": games}


@app.put("/api/games/{index}")
def update_game(index: int, game: GameConfig) -> dict[str, Any]:
    games = _read_config()
    if index < 0 or index >= len(games):
        raise HTTPException(status_code=404, detail="Game slot not found")

    games[index] = game.model_dump()
    _write_config(games)
    return {"message": "Game updated", "game": games[index]}


@app.post("/api/games/{index}/toggle")
def toggle_game(index: int) -> dict[str, Any]:
    games = _read_config()
    if index < 0 or index >= len(games):
        raise HTTPException(status_code=404, detail="Game slot not found")

    games[index]["enabled"] = not bool(games[index].get("enabled"))
    _write_config(games)
    return {"message": "Toggled", "enabled": games[index]["enabled"]}


@app.post("/api/games/{index}/launch")
def launch_game(index: int) -> dict[str, Any]:
    games = _read_config()
    if index < 0 or index >= len(games):
        raise HTTPException(status_code=404, detail="Game slot not found")

    game = games[index]
    if not game.get("enabled"):
        raise HTTPException(status_code=400, detail="Game slot is disabled")

    cwd_rel = str(game.get("cwd", "")).strip()
    command = list(game.get("command", []))

    if not cwd_rel or not command:
        raise HTTPException(status_code=400, detail="Slot is missing cwd or command")

    cwd = ROOT_DIR / cwd_rel
    if not cwd.exists():
        raise HTTPException(status_code=404, detail=f"Folder not found: {cwd_rel}")

    command = [part.replace("{python}", sys.executable) for part in command]

    env = dict(os.environ)
    # Prevent run_studio.py from opening an extra browser tab when launched from Game Hub.
    if any("run_studio.py" in str(part).lower() for part in command):
        env["GAME_HUB_LAUNCH"] = "1"

    python_paths: list[str] = [str(cwd)]
    if game.get("needs_src_path"):
        python_paths.append(str(cwd / "src"))

    current = env.get("PYTHONPATH", "")
    joined = ";".join(python_paths)
    env["PYTHONPATH"] = joined if not current else f"{joined};{current}"

    creationflags = 0

    debug_info = {
        "python_exe": sys.executable,
        "cwd": str(cwd),
        "command": command,
        "env_pythonpath": env.get("PYTHONPATH", ""),
    }

    try:
        process = subprocess.Popen(
            command,
            cwd=str(cwd),
            env=env,
            creationflags=creationflags,
        )
        return {
            "message": f"Launched {game.get('name', 'game')}",
            "pid": process.pid,
            "resolved_command": command,
            "debug": debug_info,
        }
    except Exception as exc:
        debug_info["error"] = str(exc)
        return {
            "message": "Launch failed",
            "error": str(exc),
            "debug": debug_info,
            "pid": None,
        }
