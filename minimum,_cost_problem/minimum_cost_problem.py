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