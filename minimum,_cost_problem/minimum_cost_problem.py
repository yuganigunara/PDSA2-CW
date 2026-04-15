import random
import time
import os
import threading
import unittest
import io

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

import numpy as np
from scipy.optimize import linear_sum_assignment
import mysql.connector
from mysql.connector import Error

DB_CONFIG = {
    "host":     os.getenv("PDSA_DB_HOST",     "localhost"),
    "user":     os.getenv("PDSA_DB_USER",     "root"),
    "password": os.getenv("PDSA_DB_PASSWORD", ""),
    "database": os.getenv("PDSA_DB_NAME",     "pdsa_game"),
}
DB_ENABLED = True

BG_DARK    = "#0d1117"
BG_CARD    = "#161b22"
BG_CARD2   = "#1c2128"
ACCENT1    = "#00d4aa"   # teal  – Hungarian
ACCENT2    = "#f0883e"   # amber – Greedy
ACCENT3    = "#58a6ff"   # blue  – info
RED        = "#ff6b6b"
GREEN      = "#3fb950"
TEXT_PRI   = "#e6edf3"
TEXT_SEC   = "#8b949e"
BORDER     = "#30363d"

FONT_HEAD  = ("Courier New", 22, "bold")
FONT_SUB   = ("Courier New", 12, "bold")
FONT_BODY  = ("Courier New", 11)
FONT_SMALL = ("Courier New", 9)
FONT_MONO  = ("Courier New", 10)


def init_db():
    global DB_ENABLED
    try:
        cfg = {k: v for k, v in DB_CONFIG.items() if k != "database"}
        conn = mysql.connector.connect(**cfg)
        cur  = conn.cursor()
        cur.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
        cur.execute(f"USE {DB_CONFIG['database']}")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS game_rounds (
                id             INT AUTO_INCREMENT PRIMARY KEY,
                round_number   INT           NOT NULL,
                n_tasks        INT           NOT NULL,
                hungarian_cost DECIMAL(12,4) NOT NULL,
                hungarian_time DECIMAL(12,6) NOT NULL,
                greedy_cost    DECIMAL(12,4) NOT NULL,
                greedy_time    DECIMAL(12,6) NOT NULL,
                played_at      DATETIME      DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit(); cur.close(); conn.close()
        return True, "Connected"
    except Error as e:
        DB_ENABLED = False
        return False, str(e)

def save_round(rnd, n, hc, ht, gc, gt):
    if not DB_ENABLED: return
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cur  = conn.cursor()
        cur.execute("""INSERT INTO game_rounds
            (round_number,n_tasks,hungarian_cost,hungarian_time,greedy_cost,greedy_time)
            VALUES (%s,%s,%s,%s,%s,%s)""",
            (rnd, n, hc, ht, gc, gt))
        conn.commit(); cur.close(); conn.close()
    except Error: pass

def fetch_rounds():
    if not DB_ENABLED: return []
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cur  = conn.cursor()
        cur.execute("SELECT * FROM game_rounds ORDER BY played_at DESC LIMIT 50")
        rows = cur.fetchall(); cur.close(); conn.close()
        return rows
    except Error: return []

# hungarian algorithm
def hungarian_algorithm(cost_matrix):
    t0 = time.perf_counter()
    ri, ci = linear_sum_assignment(cost_matrix)
    total  = cost_matrix[ri, ci].sum()
    assign = [(int(r), int(c), float(cost_matrix[r,c])) for r,c in zip(ri,ci)]
    return total, assign, time.perf_counter()-t0

# greedy algorithm
def greedy_algorithm(cost_matrix):
    t0 = time.perf_counter()
    n  = cost_matrix.shape[0]
    pairs = sorted([(cost_matrix[i,j],i,j) for i in range(n) for j in range(n)],
                   key=lambda x: x[0])
    emp_done, task_done, assign, total = set(), set(), [], 0.0
    for cost, e, t in pairs:
        if e not in emp_done and t not in task_done:
            assign.append((e, t, float(cost)))
            total += cost
            emp_done.add(e); task_done.add(t)
        if len(assign) == n: break
    return total, assign, time.perf_counter()-t0

# unit tests
class TestAlgorithms(unittest.TestCase):
    def setUp(self):
        self.m3 = np.array([[9,2,7],[3,6,3],[4,8,5]], dtype=float)
        self.m4 = np.array([[9,2,7,8],[6,4,3,7],[5,8,1,8],[7,6,9,4]], dtype=float)
    def test_hungarian_3x3(self):
        c,_,_ = hungarian_algorithm(self.m3); self.assertAlmostEqual(c,9.0)
    def test_hungarian_4x4(self):
        c,_,_ = hungarian_algorithm(self.m4); self.assertAlmostEqual(c,13.0)
    def test_hungarian_all_assigned(self):
        n=10; m=np.random.randint(20,201,(n,n)).astype(float)
        _,a,_=hungarian_algorithm(m)
        self.assertEqual(len(set(x[0] for x in a)),n)
        self.assertEqual(len(set(x[1] for x in a)),n)
    def test_hungarian_speed(self):
        m=np.random.randint(20,201,(100,100)).astype(float)
        _,_,t=hungarian_algorithm(m); self.assertLess(t,5.0)
    def test_greedy_all_assigned(self):
        n=10; m=np.random.randint(20,201,(n,n)).astype(float)
        _,a,_=greedy_algorithm(m)
        self.assertEqual(len(set(x[0] for x in a)),n)
        self.assertEqual(len(set(x[1] for x in a)),n)
    def test_greedy_positive(self):
        m=np.random.randint(20,201,(50,50)).astype(float)
        c,_,_=greedy_algorithm(m); self.assertGreater(c,0)
    def test_greedy_bound(self):
        n=20; m=np.random.randint(20,201,(n,n)).astype(float)
        c,_,_=greedy_algorithm(m); self.assertLessEqual(c,200*n)
    def test_hungarian_leq_greedy(self):
        for _ in range(5):
            n=random.randint(5,30); m=np.random.randint(20,201,(n,n)).astype(float)
            h,_,_=hungarian_algorithm(m); g,_,_=greedy_algorithm(m)
            self.assertLessEqual(h,g+1e-6)
    def test_single(self):
        m=np.array([[42.0]]); h,_,_=hungarian_algorithm(m); self.assertEqual(h,42.0)
    def test_uniform(self):
        m=np.full((10,10),50.0); h,_,_=hungarian_algorithm(m); self.assertAlmostEqual(h,500.0)
    def test_smoke_100(self):
        m=np.random.randint(20,201,(100,100)).astype(float)
        _,ha,_=hungarian_algorithm(m); _,ga,_=greedy_algorithm(m)
        self.assertEqual(len(ha),100); self.assertEqual(len(ga),100)