from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from snake_ladder.board import BoardSetup


class DatabaseError(RuntimeError):
    """Raised when a database operation fails."""


class ResultRepository:
    def __init__(self, db_path: str = "snake_ladder.db") -> None:
        self.db_path = Path(db_path)
        self.initialize_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def initialize_schema(self) -> None:
        queries = [
            """
            CREATE TABLE IF NOT EXISTS players (
                player_id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_name TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS games (
                game_id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id INTEGER NOT NULL,
                board_size INTEGER NOT NULL,
                correct_answer INTEGER NOT NULL,
                player_answer INTEGER NOT NULL,
                is_correct INTEGER NOT NULL CHECK(is_correct IN (0, 1)),
                created_at TEXT NOT NULL,
                FOREIGN KEY(player_id) REFERENCES players(player_id)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS game_jumps (
                jump_id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id INTEGER NOT NULL,
                jump_type TEXT NOT NULL CHECK(jump_type IN ('ladder', 'snake')),
                start_cell INTEGER NOT NULL,
                end_cell INTEGER NOT NULL,
                FOREIGN KEY(game_id) REFERENCES games(game_id) ON DELETE CASCADE
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS algorithm_runs (
                run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id INTEGER NOT NULL,
                algorithm_name TEXT NOT NULL CHECK(algorithm_name IN ('BFS', 'DP')),
                minimum_throws INTEGER NOT NULL,
                time_ns INTEGER NOT NULL,
                FOREIGN KEY(game_id) REFERENCES games(game_id) ON DELETE CASCADE,
                UNIQUE(game_id, algorithm_name)
            );
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_games_created_at
            ON games(created_at DESC);
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_game_jumps_game_id
            ON game_jumps(game_id);
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_algorithm_runs_game_algo
            ON algorithm_runs(game_id, algorithm_name);
            """,
        ]
        try:
            with self._connect() as conn:
                for query in queries:
                    conn.execute(query)
        except sqlite3.Error as exc:
            raise DatabaseError("Could not initialize database schema.") from exc

    def _get_or_create_player(self, conn: sqlite3.Connection, player_name: str, now: str) -> int:
        row = conn.execute(
            "SELECT player_id FROM players WHERE player_name = ?;",
            (player_name,),
        ).fetchone()
        if row is not None:
            return int(row[0])

        cursor = conn.execute(
            "INSERT INTO players (player_name, created_at) VALUES (?, ?);",
            (player_name, now),
        )
        return int(cursor.lastrowid)

    def save_result(
        self,
        *,
        player_name: str,
        player_answer: int,
        correct_answer: int,
        bfs_time_ns: int,
        dp_time_ns: int,
        board: BoardSetup,
    ) -> int:
        now = datetime.now(timezone.utc).isoformat()
        is_correct = int(player_answer == correct_answer)

        try:
            with self._connect() as conn:
                player_id = self._get_or_create_player(conn, player_name, now)
                game_cursor = conn.execute(
                    """
                    INSERT INTO games (
                        player_id, board_size, correct_answer, player_answer, is_correct, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?);
                    """,
                    (player_id, board.size, correct_answer, player_answer, is_correct, now),
                )
                game_id = int(game_cursor.lastrowid)

                conn.executemany(
                    """
                    INSERT INTO algorithm_runs (game_id, algorithm_name, minimum_throws, time_ns)
                    VALUES (?, ?, ?, ?);
                    """,
                    [
                        (game_id, "BFS", correct_answer, bfs_time_ns),
                        (game_id, "DP", correct_answer, dp_time_ns),
                    ],
                )

                conn.executemany(
                    """
                    INSERT INTO game_jumps (game_id, jump_type, start_cell, end_cell)
                    VALUES (?, 'ladder', ?, ?);
                    """,
                    [(game_id, start, end) for start, end in board.ladders.items()],
                )
                conn.executemany(
                    """
                    INSERT INTO game_jumps (game_id, jump_type, start_cell, end_cell)
                    VALUES (?, 'snake', ?, ?);
                    """,
                    [(game_id, start, end) for start, end in board.snakes.items()],
                )
                return game_id
        except sqlite3.Error as exc:
            raise DatabaseError("Could not save game result.") from exc

    def save_correct_answer(
        self,
        *,
        player_name: str,
        answer: int,
        bfs_time_ns: int,
        dp_time_ns: int,
        board: BoardSetup,
    ) -> None:
        self.save_result(
            player_name=player_name,
            player_answer=answer,
            correct_answer=answer,
            bfs_time_ns=bfs_time_ns,
            dp_time_ns=dp_time_ns,
            board=board,
        )

    def get_result_by_game_id(self, game_id: int) -> dict[str, object] | None:
        if not isinstance(game_id, int) or game_id <= 0:
            raise ValueError("game_id must be a positive integer.")

        query = """
        SELECT
            g.game_id AS id,
            p.player_name AS player_name,
            g.player_answer AS answer,
            g.board_size AS board_size,
            g.created_at AS created_at,
            COALESCE((
                SELECT ar.time_ns
                FROM algorithm_runs ar
                WHERE ar.game_id = g.game_id AND ar.algorithm_name = 'BFS'
            ), 0) AS bfs_time_ns,
            COALESCE((
                SELECT ar.time_ns
                FROM algorithm_runs ar
                WHERE ar.game_id = g.game_id AND ar.algorithm_name = 'DP'
            ), 0) AS dp_time_ns
        FROM games g
        JOIN players p ON p.player_id = g.player_id
        WHERE g.game_id = ?;
        """

        jumps_query = """
        SELECT jump_type, start_cell, end_cell
        FROM game_jumps
        WHERE game_id = ?;
        """

        try:
            with self._connect() as conn:
                conn.row_factory = sqlite3.Row
                row = conn.execute(query, (game_id,)).fetchone()
                if row is None:
                    return None
                jump_rows = conn.execute(jumps_query, (game_id,)).fetchall()
        except sqlite3.Error as exc:
            raise DatabaseError("Could not load saved result.") from exc

        ladders: dict[int, int] = {}
        snakes: dict[int, int] = {}
        for jump in jump_rows:
            start = int(jump["start_cell"])
            end = int(jump["end_cell"])
            if jump["jump_type"] == "ladder":
                ladders[start] = end
            else:
                snakes[start] = end

        return {
            "id": row["id"],
            "player_name": row["player_name"],
            "answer": row["answer"],
            "bfs_time_ns": row["bfs_time_ns"],
            "dp_time_ns": row["dp_time_ns"],
            "board_size": row["board_size"],
            "ladders": ladders,
            "snakes": snakes,
            "created_at": row["created_at"],
        }

    def get_recent_results(self, limit: int = 50) -> list[dict[str, object]]:
        if not isinstance(limit, int) or limit <= 0:
            raise ValueError("Limit must be a positive integer.")

        query = """
        SELECT
            g.game_id AS id,
            p.player_name AS player_name,
            g.player_answer AS answer,
            g.board_size AS board_size,
            g.created_at AS created_at,
            COALESCE((
                SELECT ar.time_ns
                FROM algorithm_runs ar
                WHERE ar.game_id = g.game_id AND ar.algorithm_name = 'BFS'
            ), 0) AS bfs_time_ns,
            COALESCE((
                SELECT ar.time_ns
                FROM algorithm_runs ar
                WHERE ar.game_id = g.game_id AND ar.algorithm_name = 'DP'
            ), 0) AS dp_time_ns
        FROM games g
        JOIN players p ON p.player_id = g.player_id
        WHERE g.is_correct = 1
        ORDER BY g.game_id DESC
        LIMIT ?;
        """

        jumps_query = """
        SELECT game_id, jump_type, start_cell, end_cell
        FROM game_jumps
        WHERE game_id IN ({placeholders});
        """

        try:
            with self._connect() as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(query, (limit,)).fetchall()

                if not rows:
                    return []

                game_ids = [int(row["id"]) for row in rows]
                placeholders = ",".join("?" for _ in game_ids)
                jump_rows = conn.execute(
                    jumps_query.format(placeholders=placeholders),
                    game_ids,
                ).fetchall()
        except sqlite3.Error as exc:
            raise DatabaseError("Could not load recent results.") from exc

        ladders_by_game: dict[int, dict[int, int]] = {game_id: {} for game_id in game_ids}
        snakes_by_game: dict[int, dict[int, int]] = {game_id: {} for game_id in game_ids}

        for jump in jump_rows:
            game_id = int(jump["game_id"])
            start = int(jump["start_cell"])
            end = int(jump["end_cell"])
            if jump["jump_type"] == "ladder":
                ladders_by_game[game_id][start] = end
            else:
                snakes_by_game[game_id][start] = end

        return [
            {
                "id": row["id"],
                "player_name": row["player_name"],
                "answer": row["answer"],
                "bfs_time_ns": row["bfs_time_ns"],
                "dp_time_ns": row["dp_time_ns"],
                "board_size": row["board_size"],
                "ladders": ladders_by_game[int(row["id"])],
                "snakes": snakes_by_game[int(row["id"])],
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    def get_database_snapshot(self) -> dict[str, list[dict[str, object]]]:
        queries = {
            "players": """
                SELECT player_id, player_name, created_at
                FROM players
                ORDER BY player_id DESC;
            """,
            "games": """
                SELECT game_id, player_id, board_size, correct_answer, player_answer, is_correct, created_at
                FROM games
                ORDER BY game_id DESC;
            """,
            "game_jumps": """
                SELECT jump_id, game_id, jump_type, start_cell, end_cell
                FROM game_jumps
                ORDER BY jump_id DESC;
            """,
            "algorithm_runs": """
                SELECT run_id, game_id, algorithm_name, minimum_throws, time_ns
                FROM algorithm_runs
                ORDER BY run_id DESC;
            """,
        }

        try:
            with self._connect() as conn:
                conn.row_factory = sqlite3.Row
                return {
                    table_name: [dict(row) for row in conn.execute(query).fetchall()]
                    for table_name, query in queries.items()
                }
        except sqlite3.Error as exc:
            raise DatabaseError("Could not load database snapshot.") from exc
