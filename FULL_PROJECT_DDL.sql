-- Consolidated SQLite DDL extracted from this workspace.
-- Projects included:
-- - Traffic simulation Problem
-- - knight's tour Problem (Python)
-- - snake
-- Verified against source schemas on: 2026-04-17
--
-- Note: game-hub-react only reads existing SQLite databases and does not define its own tables.

-- ============================================================
-- Traffic simulation Problem
-- Database file: traffic_game.db
-- Source: backend/app/storage.py
-- ============================================================

CREATE TABLE IF NOT EXISTS rounds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    capacities_json TEXT NOT NULL,
    correct_max_flow INTEGER NOT NULL,
    ff_time_ms REAL NOT NULL,
    ek_time_ms REAL NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS wins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_name TEXT NOT NULL,
    answer INTEGER NOT NULL,
    round_id INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(round_id) REFERENCES rounds(id)
);

-- ============================================================
-- knight's tour Problem (Python)
-- Database file: .knights_tour.db
-- Source: backend/knighttour/storage.py
-- ============================================================

CREATE TABLE IF NOT EXISTS winners (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player TEXT NOT NULL,
    size INTEGER NOT NULL,
    start TEXT NOT NULL,
    path_length INTEGER NOT NULL,
    timestamp TEXT NOT NULL,
    sequence_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS round_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player TEXT NOT NULL,
    size INTEGER NOT NULL,
    start TEXT NOT NULL,
    score INTEGER NOT NULL,
    result TEXT NOT NULL,
    timestamp TEXT NOT NULL
);

-- ============================================================
-- snake
-- Database file: snake_ladder.db
-- Source: snake_ladder/database.py
-- ============================================================

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

CREATE TABLE IF NOT EXISTS queens_correct_answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_name TEXT NOT NULL,
    answer INTEGER NOT NULL,
    cycle_id INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(answer, cycle_id)
);

CREATE TABLE IF NOT EXISTS queens_state (
    singleton_id INTEGER PRIMARY KEY CHECK (singleton_id = 1),
    current_cycle INTEGER NOT NULL
);

INSERT OR IGNORE INTO queens_state (singleton_id, current_cycle)
VALUES (1, 1);
