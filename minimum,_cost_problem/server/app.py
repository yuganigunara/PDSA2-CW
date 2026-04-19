from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np
import random
import time
import sqlite3
import json
import unittest
from typing import Optional
from scipy.optimize import linear_sum_assignment

app = FastAPI(title="Minimum Cost Assignment Game")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "game.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
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
        )
    """)
    conn.commit()
    conn.close()

init_db()

def hungarian_algorithm(cost_matrix: list[list[float]]) -> tuple[list[int], float, float]:
    """
    Hungarian Algorithm (Munkres) via scipy.
    Guarantees the globally optimal (minimum cost) assignment.
    Time complexity: O(n^3)
    Returns: (assignment list, total cost, elapsed ms)
    """
    start = time.perf_counter()
    matrix = np.array(cost_matrix)
    row_ind, col_ind = linear_sum_assignment(matrix)
    total_cost = float(matrix[row_ind, col_ind].sum())
    elapsed_ms = (time.perf_counter() - start) * 1000
    assignment = col_ind.tolist()
    return assignment, total_cost, round(elapsed_ms, 4)

# Greedy Algorithm
def greedy_algorithm(cost_matrix: list[list[float]]) -> tuple[list[int], float, float]:
    """
    Greedy Algorithm.
    Assigns each task to the cheapest available employee iteratively.
    Time complexity: O(n^2 log n)  — fast but sub-optimal.
    Returns: (assignment list, total cost, elapsed ms)
    """
    start = time.perf_counter()
    n = len(cost_matrix)
    assignment = [-1] * n
    assigned_employees = set()
    total_cost = 0.0

    pairs = [
        (cost_matrix[task][emp], task, emp)
        for task in range(n)
        for emp in range(n)
    ]
    pairs.sort(key=lambda x: x[0])

    assigned_tasks = set()
    for cost, task, emp in pairs:
        if task not in assigned_tasks and emp not in assigned_employees:
            assignment[task] = emp
            assigned_employees.add(emp)
            assigned_tasks.add(task)
            total_cost += cost
        if len(assigned_tasks) == n:
            break

    elapsed_ms = (time.perf_counter() - start) * 1000
    return assignment, round(total_cost, 2), round(elapsed_ms, 4)

class GameRequest(BaseModel):
    n: Optional[int] = None  # if None, random between 50–100


class GameResult(BaseModel):
    round_id: int
    n: int
    hungarian_assignment: list[int]
    hungarian_cost: float
    hungarian_time_ms: float
    greedy_assignment: list[int]
    greedy_cost: float
    greedy_time_ms: float
    winner: str
    cost_matrix_preview: list[list[float]]  # first 5x5 for display


@app.get("/")
def root():
    return {"message": "Minimum Cost Assignment Game API"}


@app.post("/api/game/play", response_model=GameResult)
def play_game(req: GameRequest):
   
    n = req.n if req.n and 50 <= req.n <= 100 else random.randint(50, 100)

    # Generate random cost matrix
    cost_matrix = [
        [round(random.uniform(20, 200), 2) for _ in range(n)]
        for _ in range(n)
    ]

    # Run algorithms
    h_assign, h_cost, h_time = hungarian_algorithm(cost_matrix)
    g_assign, g_cost, g_time = greedy_algorithm(cost_matrix)

    winner = "Hungarian" if h_cost <= g_cost else "Greedy"

    # Persist to DB
    conn = get_db()
    cursor = conn.execute(
        """INSERT INTO game_rounds
           (n, cost_matrix, hungarian_assignment, hungarian_cost, hungarian_time_ms,
            greedy_assignment, greedy_cost, greedy_time_ms, winner)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            n,
            json.dumps(cost_matrix),
            json.dumps(h_assign),
            h_cost,
            h_time,
            json.dumps(g_assign),
            g_cost,
            g_time,
            winner,
        ),
    )
    round_id = cursor.lastrowid
    conn.commit()
    conn.close()

    # Return first 5x5 preview of cost matrix
    preview = [row[:5] for row in cost_matrix[:5]]

    return GameResult(
        round_id=round_id,
        n=n,
        hungarian_assignment=h_assign,
        hungarian_cost=h_cost,
        hungarian_time_ms=h_time,
        greedy_assignment=g_assign,
        greedy_cost=g_cost,
        greedy_time_ms=g_time,
        winner=winner,
        cost_matrix_preview=preview,
    )

@app.get("/api/game/history")
def get_history(limit: int = 10):
    # Fetch recent game rounds from the db
    conn = get_db()
    rows = conn.execute(
        """SELECT id, n, hungarian_cost, hungarian_time_ms,
                  greedy_cost, greedy_time_ms, winner, played_at
           FROM game_rounds ORDER BY id DESC LIMIT ?""",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/api/game/round/{round_id}")
def get_round(round_id: int):
    # Retrieve full details of a specific round using its ID
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM game_rounds WHERE id = ?", (round_id,)
    ).fetchone()
    conn.close()

    # Return error if the round does not exist
    if not row:
        raise HTTPException(status_code=404, detail="Round not found")

    data = dict(row)

    # Convert json strings back to python lists
    data["cost_matrix"] = json.loads(data["cost_matrix"])
    data["hungarian_assignment"] = json.loads(data["hungarian_assignment"])
    data["greedy_assignment"] = json.loads(data["greedy_assignment"])

    return data


@app.get("/api/game/stats")
def get_stats():
    # Generate overall statistics across all game rounds
    conn = get_db()
    stats = conn.execute(
        """SELECT
             COUNT(*) as total_rounds,
             AVG(hungarian_cost) as avg_hungarian_cost,
             AVG(greedy_cost) as avg_greedy_cost,
             AVG(hungarian_time_ms) as avg_hungarian_time_ms,
             AVG(greedy_time_ms) as avg_greedy_time_ms,
             SUM(CASE WHEN winner='Hungarian' THEN 1 ELSE 0 END) as hungarian_wins,
             SUM(CASE WHEN winner='Greedy' THEN 1 ELSE 0 END) as greedy_wins,
             MIN(n) as min_n,
             MAX(n) as max_n
           FROM game_rounds"""
    ).fetchone()
    conn.close()

    return dict(stats)

# unit tests
class TestAlgorithms(unittest.TestCase):

    def setUp(self):
        # small matrix with known optimal result
        self.simple_matrix = [
            [5, 1, 8],
            [2, 7, 4],
            [6, 3, 3],
        ]

    def test_hungarian_optimal_small(self):
        # check hungarian works on small case
        assignment, cost, _ = hungarian_algorithm(self.simple_matrix)
        self.assertEqual(len(assignment), 3)
        self.assertEqual(len(set(assignment)), 3, "each employee once")
        self.assertAlmostEqual(cost, 6.0, places=1)

    def test_greedy_valid_assignment(self):
        # check greedy gives valid output
        assignment, cost, _ = greedy_algorithm(self.simple_matrix)
        self.assertEqual(len(assignment), 3)
        self.assertEqual(len(set(assignment)), 3, "each employee once")
        self.assertGreater(cost, 0)

    def test_hungarian_beats_or_equals_greedy(self):
        # compare hungarian and greedy performance on random data
        for _ in range(20):
            n = random.randint(5, 20)
            matrix = [[random.uniform(20, 200) for _ in range(n)] for _ in range(n)]

            _, h_cost, _ = hungarian_algorithm(matrix)
            _, g_cost, _ = greedy_algorithm(matrix)

            self.assertLessEqual(
                round(h_cost, 2),
                round(g_cost, 2),
                f"hungarian ({h_cost}) <= greedy ({g_cost})",
            )

    def test_random_large_matrix(self):
        # test with large input
        n = 100
        matrix = [[random.uniform(20, 200) for _ in range(n)] for _ in range(n)]

        h_assign, h_cost, h_time = hungarian_algorithm(matrix)
        g_assign, g_cost, g_time = greedy_algorithm(matrix)

        self.assertEqual(len(h_assign), n)
        self.assertEqual(len(g_assign), n)
        self.assertGreater(h_time, 0)
        self.assertGreater(g_time, 0)

    def test_uniform_cost_matrix(self):
        # test with all equal cost values
        n = 4
        matrix = [[50.0] * n for _ in range(n)]

        h_assign, h_cost, _ = hungarian_algorithm(matrix)
        g_assign, g_cost, _ = greedy_algorithm(matrix)

        self.assertAlmostEqual(h_cost, 200.0)
        self.assertAlmostEqual(g_cost, 200.0)

    def test_assignment_uniqueness(self):
        # ensure unique assignments (no duplicates)
        for _ in range(10):
            n = random.randint(10, 50)
            matrix = [[random.uniform(20, 200) for _ in range(n)] for _ in range(n)]

            h_assign, _, _ = hungarian_algorithm(matrix)
            g_assign, _, _ = greedy_algorithm(matrix)

            self.assertEqual(len(set(h_assign)), n)
            self.assertEqual(len(set(g_assign)), n)

    def test_cost_range(self):
        # verify cost matches matrix values
        n = 10
        matrix = [[random.uniform(20, 200) for _ in range(n)] for _ in range(n)]

        h_assign, h_cost, _ = hungarian_algorithm(matrix)
        actual_cost = sum(matrix[task][h_assign[task]] for task in range(n))

        self.assertAlmostEqual(h_cost, actual_cost, places=1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
