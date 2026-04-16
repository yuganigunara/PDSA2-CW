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


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Minimum Cost Task Assignment — PDSA CW")
        self.geometry("1100x720")
        self.minsize(900, 620)
        self.configure(bg=BG_DARK)
        self.round_number = 1
        self._build_ui()
        self._init_db_async()

    def _init_db_async(self):
        def task():
            ok, msg = init_db()
            self.after(0, lambda: self._on_db_ready(ok, msg))
        threading.Thread(target=task, daemon=True).start()

    def _on_db_ready(self, ok, msg):
        if ok:
            self._set_status("✅  MySQL connected  —  pdsa_game.game_rounds", GREEN)
        else:
            self._set_status(f"⚠  DB offline (no-save mode): {msg[:80]}", ACCENT2)

    def _set_status(self, txt, colour=TEXT_SEC):
        self.status_var.set(txt)
        self.status_lbl.configure(fg=colour)


    def _build_ui(self):
        # ── Top header bar
        hdr = tk.Frame(self, bg=BG_CARD, pady=10)
        hdr.pack(fill="x")
        tk.Label(hdr, text="◈  MINIMUM COST TASK ASSIGNMENT",
                 font=FONT_HEAD, bg=BG_CARD, fg=ACCENT1).pack(side="left", padx=20)
        tk.Label(hdr, text="PDSA Coursework",
                 font=FONT_SMALL, bg=BG_CARD, fg=TEXT_SEC).pack(side="right", padx=20)

        # ── Notebook tabs
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TNotebook",        background=BG_DARK,  borderwidth=0)
        style.configure("TNotebook.Tab",    background=BG_CARD2, foreground=TEXT_SEC,
                        font=FONT_SUB, padding=[16,6])
        style.map("TNotebook.Tab",
                  background=[("selected", BG_CARD)],
                  foreground=[("selected", ACCENT1)])
        style.configure("TFrame", background=BG_DARK)
        style.configure("Treeview",
                        background=BG_CARD2, foreground=TEXT_PRI,
                        fieldbackground=BG_CARD2, rowheight=24,
                        font=FONT_MONO)
        style.configure("Treeview.Heading",
                        background=BG_CARD, foreground=ACCENT1,
                        font=FONT_SUB)
        style.map("Treeview", background=[("selected","#264f78")])

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=10, pady=(6,0))

        self.tab_game    = ttk.Frame(nb)
        self.tab_history = ttk.Frame(nb)
        self.tab_tests   = ttk.Frame(nb)

        nb.add(self.tab_game,    text="  🎮  Play Round  ")
        nb.add(self.tab_history, text="  📊  History  ")
        nb.add(self.tab_tests,   text="  🧪  Unit Tests  ")

        self._build_game_tab()
        self._build_history_tab()
        self._build_tests_tab()

        # ── Status bar
        bar = tk.Frame(self, bg=BG_CARD, pady=4)
        bar.pack(fill="x", side="bottom")
        self.status_var = tk.StringVar(value="⏳  Connecting to MySQL...")
        self.status_lbl = tk.Label(bar, textvariable=self.status_var,
                                   font=FONT_SMALL, bg=BG_CARD, fg=TEXT_SEC)
        self.status_lbl.pack(side="left", padx=12)
        tk.Label(bar, text="Hungarian  =  O(n³)   |   Greedy  =  O(n² log n)",
                 font=FONT_SMALL, bg=BG_CARD, fg=TEXT_SEC).pack(side="right", padx=12)
        
    # Tab 1 - game
    def _build_game_tab(self):
        p = self.tab_game

        # left panel: controls
        left = tk.Frame(p, bg=BG_CARD, width=280)
        left.pack(side="left", fill="y", padx=(10,4), pady=10)
        left.pack_propagate(False)

        tk.Label(left, text="ROUND SETUP", font=FONT_SUB,
                 bg=BG_CARD, fg=ACCENT1).pack(anchor="w", padx=16, pady=(14,4))

        # round indicator
        self.round_lbl = tk.Label(left, text=f"Round  #1",
                                  font=("Courier New",16,"bold"),
                                  bg=BG_CARD, fg=TEXT_PRI)
        self.round_lbl.pack(padx=16, pady=(0,12))

        # N input
        tk.Label(left, text="Number of Tasks  (N)", font=FONT_BODY,
                 bg=BG_CARD, fg=TEXT_SEC).pack(anchor="w", padx=16)

        nf = tk.Frame(left, bg=BG_CARD)
        nf.pack(fill="x", padx=16, pady=(4,0))
        self.n_var = tk.StringVar()
        tk.Entry(nf, textvariable=self.n_var, font=FONT_BODY,
                 bg=BG_CARD2, fg=TEXT_PRI, insertbackground=ACCENT1,
                 relief="flat", bd=6, width=10).pack(side="left")
        tk.Button(nf, text="Random", font=FONT_SMALL,
                  bg=BG_CARD2, fg=ACCENT3, activebackground=BORDER,
                  relief="flat", cursor="hand2",
                  command=lambda: self.n_var.set(str(random.randint(50,100)))
                  ).pack(side="left", padx=(6,0))

        tk.Label(left, text="Leave blank or click Random\nfor N ∈ [50, 100]",
                 font=FONT_SMALL, bg=BG_CARD, fg=TEXT_SEC,
                 justify="left").pack(anchor="w", padx=16, pady=(4,12))

        # run button
        self.run_btn = tk.Button(
            left, text="▶  RUN ROUND", font=FONT_SUB,
            bg=ACCENT1, fg=BG_DARK, activebackground="#00b894",
            relief="flat", cursor="hand2", padx=10, pady=8,
            command=self._run_round)
        self.run_btn.pack(fill="x", padx=16, pady=(0,16))

        # progress bar
        self.progress = ttk.Progressbar(left, mode="indeterminate", length=240)
        style = ttk.Style()
        style.configure("green.Horizontal.TProgressbar",
                        troughcolor=BG_CARD2, background=ACCENT1)
        self.progress.configure(style="green.Horizontal.TProgressbar")
        self.progress.pack(padx=16)

        # summary cards
        tk.Label(left, text="LAST ROUND SUMMARY", font=FONT_SMALL,
                 bg=BG_CARD, fg=TEXT_SEC).pack(anchor="w", padx=16, pady=(16,4))

        self._make_summary_card(left, "Hungarian", ACCENT1, "h")
        self._make_summary_card(left, "Greedy",    ACCENT2, "g")

        # winner badge
        self.winner_var = tk.StringVar(value="—")
        tk.Label(left, textvariable=self.winner_var,
                 font=("Courier New",10,"bold"), bg=BG_CARD, fg=GREEN,
                 wraplength=240, justify="center").pack(padx=16, pady=(8,0))

        # right panel: results
        right = tk.Frame(p, bg=BG_DARK)
        right.pack(side="left", fill="both", expand=True, padx=(4,10), pady=10)

        # two assignment tables side by side
        tables_frame = tk.Frame(right, bg=BG_DARK)
        tables_frame.pack(fill="both", expand=True)

        self.h_tree = self._make_assign_tree(tables_frame, "🟢  Hungarian Assignments", ACCENT1)
        self.g_tree = self._make_assign_tree(tables_frame, "🟠  Greedy Assignments",    ACCENT2)

        # log box at the bottom
        tk.Label(right, text="EXECUTION LOG", font=FONT_SMALL,
                 bg=BG_DARK, fg=TEXT_SEC).pack(anchor="w", pady=(6,2))
        self.log_box = scrolledtext.ScrolledText(
            right, height=7, font=FONT_MONO,
            bg=BG_CARD2, fg=TEXT_PRI, insertbackground=ACCENT1,
            relief="flat", bd=6, state="disabled")
        self.log_box.pack(fill="x")
        # Tag colours for log
        self.log_box.tag_config("green",   foreground=GREEN)
        self.log_box.tag_config("teal",    foreground=ACCENT1)
        self.log_box.tag_config("amber",   foreground=ACCENT2)
        self.log_box.tag_config("blue",    foreground=ACCENT3)
        self.log_box.tag_config("red",     foreground=RED)
        self.log_box.tag_config("dim",     foreground=TEXT_SEC)

    def _make_summary_card(self, parent, label, colour, prefix):
        f = tk.Frame(parent, bg=BG_CARD2, pady=6)
        f.pack(fill="x", padx=16, pady=3)
        tk.Label(f, text=label, font=FONT_SMALL, bg=BG_CARD2, fg=colour
                 ).grid(row=0, column=0, sticky="w", padx=8)
        cost_var = tk.StringVar(value="$—")
        time_var = tk.StringVar(value="— ms")
        tk.Label(f, textvariable=cost_var, font=("Courier New",11,"bold"),
                 bg=BG_CARD2, fg=TEXT_PRI).grid(row=1, column=0, sticky="w", padx=8)
        tk.Label(f, textvariable=time_var, font=FONT_SMALL,
                 bg=BG_CARD2, fg=TEXT_SEC).grid(row=2, column=0, sticky="w", padx=8)
        setattr(self, f"{prefix}_cost_var", cost_var)
        setattr(self, f"{prefix}_time_var", time_var)

    def _make_assign_tree(self, parent, title, colour):
        frame = tk.Frame(parent, bg=BG_DARK)
        frame.pack(side="left", fill="both", expand=True, padx=4)
        tk.Label(frame, text=title, font=FONT_SUB,
                 bg=BG_DARK, fg=colour).pack(anchor="w", pady=(0,4))
        cols = ("Employee", "Task", "Cost ($)")
        tree = ttk.Treeview(frame, columns=cols, show="headings", height=14)
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=90, anchor="center")
        sb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        return tree
