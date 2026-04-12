from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

DEFAULT_STORAGE_FILE = Path(".knights_tour.db")


def _connect(storage_file: Path | str) -> sqlite3.Connection:
    db_path = Path(storage_file)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(db_path)


def _ensure_schema(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS winners (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player TEXT NOT NULL,
            size INTEGER NOT NULL,
            start TEXT NOT NULL,
            path_length INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            sequence_json TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS round_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player TEXT NOT NULL,
            size INTEGER NOT NULL,
            start TEXT NOT NULL,
            score INTEGER NOT NULL,
            result TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
        """
    )
    connection.commit()


def get_winners(storage_file: Path | str = DEFAULT_STORAGE_FILE) -> list[dict[str, Any]]:
    try:
        connection = _connect(storage_file)
        try:
            _ensure_schema(connection)
            rows = connection.execute(
                """
                SELECT player, size, start, path_length, timestamp, sequence_json
                FROM winners
                ORDER BY id DESC
                LIMIT 15
                """
            ).fetchall()
        finally:
            connection.close()

        winners: list[dict[str, Any]] = []
        for player, size, start, path_length, timestamp, sequence_json in rows:
            try:
                sequence = json.loads(sequence_json)
                if not isinstance(sequence, list):
                    sequence = []
            except json.JSONDecodeError:
                sequence = []

            winners.append(
                {
                    "player": player,
                    "size": size,
                    "start": start,
                    "pathLength": path_length,
                    "timestamp": timestamp,
                    "sequence": sequence,
                }
            )
        return winners
    except (OSError, sqlite3.DatabaseError):
        return []


def save_winner(entry: dict[str, Any], storage_file: Path | str = DEFAULT_STORAGE_FILE) -> None:
    player = str(entry.get("player", "Anonymous"))
    size = int(entry.get("size", 8))
    start = str(entry.get("start", "(1, 1)"))
    path_length = int(entry.get("pathLength", 0))
    timestamp = str(entry.get("timestamp", ""))
    sequence = entry.get("sequence", [])
    if not isinstance(sequence, list):
        sequence = []

    try:
        connection = _connect(storage_file)
        try:
            _ensure_schema(connection)
            connection.execute(
                """
                INSERT INTO winners (player, size, start, path_length, timestamp, sequence_json)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (player, size, start, path_length, timestamp, json.dumps(sequence)),
            )
            connection.execute(
                """
                DELETE FROM winners
                WHERE id NOT IN (SELECT id FROM winners ORDER BY id DESC LIMIT 15)
                """
            )
            connection.commit()
        finally:
            connection.close()
    except (OSError, ValueError, TypeError, sqlite3.DatabaseError):
        # Best effort persistence: gameplay should continue even if database write fails.
        return


def get_round_scores(storage_file: Path | str = DEFAULT_STORAGE_FILE) -> list[dict[str, Any]]:
    try:
        connection = _connect(storage_file)
        try:
            _ensure_schema(connection)
            legacy_rows = connection.execute(
                """
                SELECT player, size, start, path_length, timestamp
                FROM winners
                ORDER BY id DESC
                LIMIT 30
                """
            ).fetchall()

            inserted = 0
            for player, size, start, path_length, timestamp in legacy_rows:
                existing = connection.execute(
                    """
                    SELECT 1 FROM round_scores
                    WHERE player = ? AND size = ? AND start = ? AND score = ? AND result = 'win' AND timestamp = ?
                    LIMIT 1
                    """,
                    (player, int(size), start, int(path_length), timestamp),
                ).fetchone()
                if existing:
                    continue

                connection.execute(
                    """
                    INSERT INTO round_scores (player, size, start, score, result, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (player, int(size), start, int(path_length), "win", timestamp),
                )
                inserted += 1

            if inserted > 0:
                connection.commit()

            rows = connection.execute(
                """
                SELECT player, size, start, score, result, timestamp
                FROM round_scores
                ORDER BY id DESC
                LIMIT 30
                """
            ).fetchall()
        finally:
            connection.close()

        return [
            {
                "player": player,
                "size": size,
                "start": start,
                "score": score,
                "result": result,
                "timestamp": timestamp,
            }
            for player, size, start, score, result, timestamp in rows
        ]
    except (OSError, sqlite3.DatabaseError):
        return []


def save_round_score(entry: dict[str, Any], storage_file: Path | str = DEFAULT_STORAGE_FILE) -> None:
    player = str(entry.get("player", "Player"))
    size = int(entry.get("size", 8))
    start = str(entry.get("start", "(1, 1)"))
    score = int(entry.get("score", 0))
    result = str(entry.get("result", "draw"))
    timestamp = str(entry.get("timestamp", ""))

    if result not in {"win", "lose", "draw"}:
        result = "draw"

    try:
        connection = _connect(storage_file)
        try:
            _ensure_schema(connection)
            connection.execute(
                """
                INSERT INTO round_scores (player, size, start, score, result, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (player, size, start, score, result, timestamp),
            )
            connection.execute(
                """
                DELETE FROM round_scores
                WHERE id NOT IN (SELECT id FROM round_scores ORDER BY id DESC LIMIT 30)
                """
            )
            connection.commit()
        finally:
            connection.close()
    except (OSError, ValueError, TypeError, sqlite3.DatabaseError):
        return
