-- Consolidated SQLite DDL extracted from this workspace.
-- Projects included:
-- - Traffic simulation Problem
-- - knight's tour Problem (Python)
-- - sixteen queens
-- - snake
-- - minimum,_cost_problem
-- Verified against source schemas on: 2026-04-20
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
-- sixteen queens
-- Database file: data/sixteen_queens.db
-- Source: sixteen queens/backend/app/db.py
-- ============================================================

CREATE TABLE IF NOT EXISTS queens_rounds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    round_no INTEGER NOT NULL,
    algorithm TEXT NOT NULL,
    solutions INTEGER NOT NULL,
    time_ns INTEGER NOT NULL,
    peak_bytes INTEGER NOT NULL,
    board_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS queens_answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    round_no INTEGER NOT NULL,
    player_name TEXT NOT NULL,
    answer INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(round_no, answer)
);

CREATE TABLE IF NOT EXISTS queens_state (
    singleton_id INTEGER PRIMARY KEY CHECK (singleton_id = 1),
    current_round INTEGER NOT NULL DEFAULT 0,
    recognized INTEGER NOT NULL DEFAULT 0
);

INSERT OR IGNORE INTO queens_state (singleton_id, current_round, recognized)
VALUES (1, 0, 0);

-- ============================================================
-- snake
-- Database file: snake_ladder.db
-- Source: snake/snake_ladder/database.py
-- ============================================================

CREATE TABLE IF NOT EXISTS players (
    player_id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_name TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL
);

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

CREATE TABLE IF NOT EXISTS game_jumps (
    jump_id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id INTEGER NOT NULL,
    jump_type TEXT NOT NULL CHECK(jump_type IN ('ladder', 'snake')),
    start_cell INTEGER NOT NULL,
    end_cell INTEGER NOT NULL,
    FOREIGN KEY(game_id) REFERENCES games(game_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS algorithm_runs (
    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id INTEGER NOT NULL,
    algorithm_name TEXT NOT NULL CHECK(algorithm_name IN ('BFS', 'DP')),
    minimum_throws INTEGER NOT NULL,
    time_ns INTEGER NOT NULL,
    FOREIGN KEY(game_id) REFERENCES games(game_id) ON DELETE CASCADE,
    UNIQUE(game_id, algorithm_name)
);

CREATE INDEX IF NOT EXISTS idx_games_created_at
ON games(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_game_jumps_game_id
ON game_jumps(game_id);

CREATE INDEX IF NOT EXISTS idx_algorithm_runs_game_algo
ON algorithm_runs(game_id, algorithm_name);

-- ============================================================
-- minimum,_cost_problem
-- Database file: game.db
-- Source: minimum,_cost_problem/server/app.py
-- ============================================================

CREATE TABLE IF NOT EXISTS game_rounds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    n INTEGER NOT NULL,
    cost_matrix TEXT NOT NULL,
    hungarian_assignment TEXT,
    hungarian_cost REAL,
    hungarian_time_ms REAL,
    greedy_assignment TEXT,
    greedy_cost REAL,
    greedy_time_ms REAL,
    winner TEXT,
    played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
