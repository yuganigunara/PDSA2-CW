import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List


def _connect(db_path: Path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path):
    with _connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS rounds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                capacities_json TEXT NOT NULL,
                correct_max_flow INTEGER NOT NULL,
                ff_time_ms REAL NOT NULL,
                ek_time_ms REAL NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS wins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_name TEXT NOT NULL,
                answer INTEGER NOT NULL,
                round_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(round_id) REFERENCES rounds(id)
            )
            """
        )


def save_round(db_path: Path, capacities: Dict[str, int], correct_max_flow: int, ff_time_ms: float, ek_time_ms: float) -> int:
    with _connect(db_path) as conn:
        cur = conn.execute(
            """
            INSERT INTO rounds (capacities_json, correct_max_flow, ff_time_ms, ek_time_ms, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                json.dumps(capacities),
                correct_max_flow,
                ff_time_ms,
                ek_time_ms,
                datetime.utcnow().isoformat(),
            ),
        )
        return cur.lastrowid


def get_round(db_path: Path, round_id: int):
    with _connect(db_path) as conn:
        row = conn.execute("SELECT * FROM rounds WHERE id = ?", (round_id,)).fetchone()
        return row


def save_win(db_path: Path, player_name: str, answer: int, round_id: int):
    with _connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO wins (player_name, answer, round_id, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (player_name.strip(), answer, round_id, datetime.utcnow().isoformat()),
        )


def get_leaderboard(db_path: Path, limit: int = 10) -> List[sqlite3.Row]:
    with _connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT player_name, COUNT(*) AS wins
            FROM wins
            GROUP BY player_name
            ORDER BY wins DESC, player_name ASC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return rows
