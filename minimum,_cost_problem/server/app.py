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