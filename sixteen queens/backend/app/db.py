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
                    queen_count integer not null default 16,
                    player_name text not null,
                    answer integer not null,
                    created_at text not null,
                    unique(round_no, queen_count, answer)
                );
                create table if not exists queens_modes (
                    queen_count integer primary key,
                    current_round integer not null default 0,
                    recognized integer not null default 0
                );
                insert or ignore into queens_modes (queen_count, current_round, recognized) values (8, 0, 0);
                insert or ignore into queens_modes (queen_count, current_round, recognized) values (16, 0, 0);
                """
            )
            self._add_column_if_missing(conn, "queens_rounds", "queen_count integer not null default 16")
            self._add_column_if_missing(conn, "queens_answers", "queen_count integer not null default 16")

    def _add_column_if_missing(self, conn: sqlite3.Connection, table: str, column_def: str) -> None:
        column_name = column_def.split()[0]
        existing = {row[1] for row in conn.execute(f"pragma table_info({table})")}
        if column_name not in existing:
            conn.execute(f"alter table {table} add column {column_def}")

    def _ensure_mode_row(self, conn: sqlite3.Connection, queen_count: int) -> None:
        conn.execute("insert or ignore into queens_modes (queen_count, current_round, recognized) values (?, 0, 0)", (queen_count,))

    def next_round(self, queen_count: int) -> int:
        with self._connect() as conn:
            self._ensure_mode_row(conn, queen_count)
            row = conn.execute("select current_round from queens_modes where queen_count = ?", (queen_count,)).fetchone()
            round_no = int(row[0]) + 1
            conn.execute("update queens_modes set current_round = ?, recognized = 0 where queen_count = ?", (round_no, queen_count))
            return round_no

    def current_round(self, queen_count: int) -> int:
        with self._connect() as conn:
            self._ensure_mode_row(conn, queen_count)
            row = conn.execute("select current_round from queens_modes where queen_count = ?", (queen_count,)).fetchone()
            return int(row[0])

    def is_recognized(self, round_no: int, queen_count: int, answer: int) -> bool:
        with self._connect() as conn:
            row = conn.execute("select 1 from queens_answers where round_no = ? and queen_count = ? and answer = ?", (round_no, queen_count, answer)).fetchone()
            return row is not None

    def save_answer(self, round_no: int, queen_count: int, player_name: str, answer: int) -> None:
        with self._connect() as conn:
            conn.execute(
                "insert or ignore into queens_answers (round_no, queen_count, player_name, answer, created_at) values (?, ?, ?, ?, ?)",
                (round_no, queen_count, player_name, answer, datetime.utcnow().isoformat()),
            )
            conn.execute("update queens_modes set recognized = 1 where queen_count = ?", (queen_count,))

    def save_round(self, queen_count: int, result: BenchmarkResult, board: list[str]) -> None:
        with self._connect() as conn:
            conn.execute(
                "insert into queens_rounds (round_no, queen_count, algorithm, solutions, time_ns, peak_bytes, board_json, created_at) values (?, ?, ?, ?, ?, ?, ?, ?)",
                (result.round_no, queen_count, result.algorithm, result.solutions, result.time_ns, result.peak_bytes, json.dumps(board), datetime.utcnow().isoformat()),
            )

    def dashboard(self, queen_count: int, limit: int | None = None) -> dict:
        with self._connect() as conn:
            self._ensure_mode_row(conn, queen_count)
            if limit is None:
                rows = conn.execute(
                    "select round_no, queen_count, algorithm, solutions, time_ns, peak_bytes, board_json, created_at from queens_rounds where queen_count = ? order by id desc",
                    (queen_count,)
                ).fetchall()
                answers = conn.execute(
                    "select round_no, queen_count, player_name, answer, created_at from queens_answers where queen_count = ? order by id desc",
                    (queen_count,)
                ).fetchall()
            else:
                rows = conn.execute(
                    "select round_no, queen_count, algorithm, solutions, time_ns, peak_bytes, board_json, created_at from queens_rounds where queen_count = ? order by id desc limit ?",
                    (queen_count, limit * 2),
                ).fetchall()
                answers = conn.execute(
                    "select round_no, queen_count, player_name, answer, created_at from queens_answers where queen_count = ? order by id desc limit ?",
                    (queen_count, limit),
                ).fetchall()
        return {"rounds": [dict(row) for row in rows][::-1], "answers": [dict(row) for row in answers][::-1]}
