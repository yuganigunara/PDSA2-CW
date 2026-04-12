from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from snake_ladder.board import BoardSetup
from snake_ladder.queens import QueensBenchmarkResult


class DatabaseError(RuntimeError):
    """Raised when a database operation fails."""


class ResultRepository:
    def __init__(self, db_path: str = "snake_ladder.db") -> None:
        self.db_path = Path(db_path)
        self._init_schema()
        self._init_queens_schema()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_schema(self) -> None:
        query = """
        CREATE TABLE IF NOT EXISTS game_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_name TEXT NOT NULL,
            answer INTEGER NOT NULL,
            bfs_time_ns INTEGER NOT NULL,
            dp_time_ns INTEGER NOT NULL,
            board_size INTEGER NOT NULL,
            ladders_json TEXT NOT NULL,
            snakes_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        """
        try:
            with self._connect() as conn:
                conn.execute(query)
        except sqlite3.Error as exc:
            raise DatabaseError("Could not initialize database schema.") from exc

    def _init_queens_schema(self) -> None:
        benchmark_query = """
        CREATE TABLE IF NOT EXISTS queens_benchmarks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            board_size INTEGER NOT NULL,
            queens_count INTEGER NOT NULL,
            sequential_solutions INTEGER NOT NULL,
            sequential_time_ns INTEGER NOT NULL,
            threaded_solutions INTEGER NOT NULL,
            threaded_time_ns INTEGER NOT NULL,
            created_at TEXT NOT NULL
        );
        """
        answer_query = """
        CREATE TABLE IF NOT EXISTS queens_correct_answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_name TEXT NOT NULL,
            answer INTEGER NOT NULL,
            cycle_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(answer, cycle_id)
        );
        """
        state_query = """
        CREATE TABLE IF NOT EXISTS queens_state (
            singleton_id INTEGER PRIMARY KEY CHECK (singleton_id = 1),
            current_cycle INTEGER NOT NULL
        );
        """
        seed_state_query = """
        INSERT OR IGNORE INTO queens_state (singleton_id, current_cycle)
        VALUES (1, 1);
        """

        try:
            with self._connect() as conn:
                conn.execute(benchmark_query)
                conn.execute(answer_query)
                conn.execute(state_query)
                conn.execute(seed_state_query)
        except sqlite3.Error as exc:
            raise DatabaseError("Could not initialize queens schema.") from exc

    def save_correct_answer(
        self,
        *,
        player_name: str,
        answer: int,
        bfs_time_ns: int,
        dp_time_ns: int,
        board: BoardSetup,
    ) -> None:
        query = """
        INSERT INTO game_results (
            player_name, answer, bfs_time_ns, dp_time_ns,
            board_size, ladders_json, snakes_json, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """

        payload = (
            player_name,
            answer,
            bfs_time_ns,
            dp_time_ns,
            board.size,
            json.dumps(board.ladders, sort_keys=True),
            json.dumps(board.snakes, sort_keys=True),
            datetime.now(timezone.utc).isoformat(),
        )

        try:
            with self._connect() as conn:
                conn.execute(query, payload)
        except sqlite3.Error as exc:
            raise DatabaseError("Could not save game result.") from exc

    def save_queens_benchmark(self, result: QueensBenchmarkResult) -> None:
        query = """
        INSERT INTO queens_benchmarks (
            board_size, queens_count, sequential_solutions, sequential_time_ns,
            threaded_solutions, threaded_time_ns, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """
        payload = (
            result.board_size,
            result.queens_count,
            result.sequential_solutions,
            result.sequential_time_ns,
            result.threaded_solutions,
            result.threaded_time_ns,
            datetime.now(timezone.utc).isoformat(),
        )
        try:
            with self._connect() as conn:
                conn.execute(query, payload)
        except sqlite3.Error as exc:
            raise DatabaseError("Could not save queens benchmark.") from exc

    def get_latest_queens_benchmark(self) -> QueensBenchmarkResult | None:
        query = """
        SELECT
            board_size,
            queens_count,
            sequential_solutions,
            sequential_time_ns,
            threaded_solutions,
            threaded_time_ns
        FROM queens_benchmarks
        ORDER BY id DESC
        LIMIT 1;
        """
        try:
            with self._connect() as conn:
                row = conn.execute(query).fetchone()
        except sqlite3.Error as exc:
            raise DatabaseError("Could not read queens benchmark.") from exc

        if row is None:
            return None

        return QueensBenchmarkResult(
            board_size=row[0],
            queens_count=row[1],
            sequential_solutions=row[2],
            sequential_time_ns=row[3],
            threaded_solutions=row[4],
            threaded_time_ns=row[5],
        )

    def get_current_queens_cycle(self) -> int:
        query = "SELECT current_cycle FROM queens_state WHERE singleton_id = 1;"
        try:
            with self._connect() as conn:
                row = conn.execute(query).fetchone()
        except sqlite3.Error as exc:
            raise DatabaseError("Could not read queens cycle state.") from exc
        if row is None:
            raise DatabaseError("Queens cycle state is missing.")
        return int(row[0])

    def has_recognized_queens_answer(self, *, answer: int, cycle_id: int) -> bool:
        query = """
        SELECT 1
        FROM queens_correct_answers
        WHERE answer = ? AND cycle_id = ?
        LIMIT 1;
        """
        try:
            with self._connect() as conn:
                row = conn.execute(query, (answer, cycle_id)).fetchone()
        except sqlite3.Error as exc:
            raise DatabaseError("Could not check queens answer recognition.") from exc
        return row is not None

    def save_queens_correct_answer(self, *, player_name: str, answer: int, cycle_id: int) -> None:
        query = """
        INSERT INTO queens_correct_answers (player_name, answer, cycle_id, created_at)
        VALUES (?, ?, ?, ?);
        """
        payload = (
            player_name,
            answer,
            cycle_id,
            datetime.now(timezone.utc).isoformat(),
        )
        try:
            with self._connect() as conn:
                conn.execute(query, payload)
        except sqlite3.IntegrityError as exc:
            raise DatabaseError("This correct response is already recognized in current cycle.") from exc
        except sqlite3.Error as exc:
            raise DatabaseError("Could not save queens correct answer.") from exc

    def reset_queens_recognition_cycle(self) -> None:
        query = """
        UPDATE queens_state
        SET current_cycle = current_cycle + 1
        WHERE singleton_id = 1;
        """
        try:
            with self._connect() as conn:
                conn.execute(query)
        except sqlite3.Error as exc:
            raise DatabaseError("Could not reset queens recognition cycle.") from exc
