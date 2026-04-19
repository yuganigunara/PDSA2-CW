from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from .threaded import BenchmarkResult

DB_PATH = Path(__file__).resolve().parents[2] / "data" / "sixteen_queens.db"


class QueensStore:
    def __init__(self, path: Path = DB_PATH) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                create table if not exists queens_rounds (
                    id integer primary key autoincrement,
                    round_no integer not null,
                    algorithm text not null,
                    solutions integer not null,
                    time_ns integer not null,
                    peak_bytes integer not null,
                    board_json text not null,
                    created_at text not null
                );
                create table if not exists queens_answers (
                    id integer primary key autoincrement,
                    round_no integer not null,
                    player_name text not null,
                    answer integer not null,
                    created_at text not null,
                    unique(round_no, answer)
                );
                create table if not exists queens_state (
                    singleton_id integer primary key check (singleton_id = 1),
                    current_round integer not null default 0,
                    recognized integer not null default 0
                );
                insert or ignore into queens_state (singleton_id, current_round, recognized) values (1, 0, 0);
                """
            )

    def next_round(self) -> int:
        with self._connect() as conn:
            row = conn.execute("select current_round from queens_state where singleton_id = 1").fetchone()
            round_no = int(row[0]) + 1
            conn.execute("update queens_state set current_round = ?, recognized = 0 where singleton_id = 1", (round_no,))
            return round_no

    def current_round(self) -> int:
        with self._connect() as conn:
            row = conn.execute("select current_round from queens_state where singleton_id = 1").fetchone()
            return int(row[0])

    def is_recognized(self, round_no: int, answer: int) -> bool:
        with self._connect() as conn:
            row = conn.execute("select 1 from queens_answers where round_no = ? and answer = ?", (round_no, answer)).fetchone()
            return row is not None

    def save_answer(self, round_no: int, player_name: str, answer: int) -> None:
        with self._connect() as conn:
            conn.execute(
                "insert or ignore into queens_answers (round_no, player_name, answer, created_at) values (?, ?, ?, ?)",
                (round_no, player_name, answer, datetime.utcnow().isoformat()),
            )
            conn.execute("update queens_state set recognized = 1 where singleton_id = 1")

    def save_round(self, result: BenchmarkResult, board: list[str]) -> None:
        with self._connect() as conn:
            conn.execute(
                "insert into queens_rounds (round_no, algorithm, solutions, time_ns, peak_bytes, board_json, created_at) values (?, ?, ?, ?, ?, ?, ?)",
                (result.round_no, result.algorithm, result.solutions, result.time_ns, result.peak_bytes, json.dumps(board), datetime.utcnow().isoformat()),
            )

    def dashboard(self, limit: int | None = None) -> dict:
        with self._connect() as conn:
            if limit is None:
                rows = conn.execute(
                    "select round_no, algorithm, solutions, time_ns, peak_bytes, board_json, created_at from queens_rounds order by id desc"
                ).fetchall()
                answers = conn.execute(
                    "select round_no, player_name, answer, created_at from queens_answers order by id desc"
                ).fetchall()
            else:
                rows = conn.execute(
                    "select round_no, algorithm, solutions, time_ns, peak_bytes, board_json, created_at from queens_rounds order by id desc limit ?",
                    (limit * 2,),
                ).fetchall()
                answers = conn.execute(
                    "select round_no, player_name, answer, created_at from queens_answers order by id desc limit ?",
                    (limit,),
                ).fetchall()
        return {"rounds": [dict(row) for row in rows][::-1], "answers": [dict(row) for row in answers][::-1]}
