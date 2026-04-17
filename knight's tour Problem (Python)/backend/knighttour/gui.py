from __future__ import annotations

import random
import threading
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

from .algorithms import Position, get_possible_moves, solve_backtracking, solve_warnsdorff, validate_path
from .storage import get_winners, save_winner

MODE_SOLO = "Solo Game"
MODE_2P = "Two Player Game"
MODE_SOLVER = "Solver Mode"


class KnightTourGUI(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Knight's Tour Game")
        self.geometry("1060x780")
        self.minsize(760, 520)
        self.configure(bg="#f1efe8")

        self.mode_var = tk.StringVar(value=MODE_SOLO)
        self.size_var = tk.StringVar(value="8")
        self.start_row_var = tk.StringVar(value="0")
        self.start_col_var = tk.StringVar(value="0")
        self.solver_var = tk.StringVar(value="warnsdorff")
        self.node_limit_var = tk.StringVar(value="3500000")
        self.turn_seconds_var = tk.StringVar(value="20")
        self.player1_var = tk.StringVar(value="Player 1")
        self.player2_var = tk.StringVar(value="Player 2")
        self.save_var = tk.BooleanVar(value=True)
        self.animate_var = tk.BooleanVar(value=True)
        self.speed_var = tk.IntVar(value=30)
        self.status_var = tk.StringVar(value="Ready. Choose mode, then start game or solver.")
        self.score_banner_var = tk.StringVar(value="Score: Player 1 0 | Player 2 0")
        self.turn_banner_var = tk.StringVar(value="Turn: - | Time Left: 0s | Lives: 3")
        self.player1_card_var = tk.StringVar(value="Player 1\nScore: 0")
        self.player2_card_var = tk.StringVar(value="Player 2\nScore: 0")
        self.fullscreen_var = tk.BooleanVar(value=True)
        self.controls_visible = True

        self.current_size = 8
        self.current_start = Position(0, 0)
        self.current_path: list[Position] = []
        self.hint_positions: list[Position] = []

        self.solving = False
        self.animation_job: str | None = None
        self.animation_index = 0
        self.timer_job: str | None = None
        self.time_left = 0

        self.game_active = False
        self.game_finished = False
        self.game_path: list[Position] = []
        self.game_visited: set[str] = set()
        self.game_owner: dict[str, int] = {}
        self.turn = 1
        self.last_mover = 0
        self.p1_score = 0
        self.p2_score = 0
        self.solo_lives = 3
        self.bonus_value = 3
        self.bonus_cells: set[str] = set()
        self.bonus_claimed: set[str] = set()

        self._board_metrics: tuple[float, float, float, float, int] | None = None

        self._build_layout()
        self._build_menu()
        self.bind("<F11>", self._toggle_fullscreen)
        self.bind("<Escape>", self._exit_fullscreen)
        self.after(60, self._apply_startup_fullscreen)
        self._draw_board(self.current_size, [], [])

    def _apply_startup_fullscreen(self) -> None:
        self.attributes("-fullscreen", True)
        self.fullscreen_var.set(True)
        self.status_var.set("Fullscreen enabled. Press F11 to toggle, Esc to exit fullscreen.")

    def _build_menu(self) -> None:
        menubar = tk.Menu(self)

        game_menu = tk.Menu(menubar, tearoff=0)
        game_menu.add_command(label="Knight's Tour Problem", command=self._activate_knights_tour_problem)
        game_menu.add_separator()
        game_menu.add_command(label="New Round", command=self._start_game)
        game_menu.add_command(label="Clear Board", command=self._clear_board)
        game_menu.add_separator()
        game_menu.add_command(label="Exit", command=self.destroy)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Rules", command=self._show_rules)

        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_checkbutton(label="Fullscreen", variable=self.fullscreen_var, command=self._toggle_fullscreen)
        view_menu.add_command(label="Toggle Panels", command=self._toggle_controls_panel)

        menubar.add_cascade(label="Game", menu=game_menu)
        menubar.add_cascade(label="View", menu=view_menu)
        menubar.add_cascade(label="Help", menu=help_menu)
        self.config(menu=menubar)

    def _toggle_fullscreen(self, _event: tk.Event | None = None) -> None:
        next_state = not bool(self.attributes("-fullscreen"))
        self.attributes("-fullscreen", next_state)
        self.fullscreen_var.set(next_state)

    def _exit_fullscreen(self, _event: tk.Event | None = None) -> None:
        self.attributes("-fullscreen", False)
        self.fullscreen_var.set(False)

    def _toggle_controls_panel(self) -> None:
        if self.controls_visible:
            self.top_controls.pack_forget()
            self.output_wrap.pack_forget()
            self.toggle_controls_button.configure(text="Show Panels")
            self.controls_visible = False
            self.status_var.set("Panels hidden to maximize board view.")
            return

        self.top_controls.pack(fill="x", padx=10, pady=(0, 6), before=self.board_wrap)
        self.output_wrap.pack(fill="x", padx=10, pady=(0, 4), before=self.footer)
        self.toggle_controls_button.configure(text="Hide Panels")
        self.controls_visible = True
        self.status_var.set("Panels shown.")

    def _activate_knights_tour_problem(self) -> None:
        self.mode_var.set(MODE_SOLO)
        self.status_var.set("Knight's Tour Problem selected. Start a new round.")
        self.summary_label.configure(
            text=(
                "Output:\n"
                "Knight's Tour Problem\n"
                "Goal: visit every square exactly once.\n"
                "Board: choose 8x8 or 16x16, then click New Game."
            )
        )

    def _build_layout(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Header.TLabel", font=("Georgia", 24, "bold"), background="#f1efe8", foreground="#20323f")
        style.configure("Sub.TLabel", font=("Georgia", 11), background="#f1efe8", foreground="#4f5f68")
        style.configure("Score.TLabel", font=("Consolas", 12, "bold"), background="#f8f6ef", foreground="#143d59")
        style.configure("Panel.TFrame", background="#f8f6ef")
        style.configure("Status.TLabel", font=("Consolas", 10), background="#f1efe8", foreground="#20323f")

        header = ttk.Frame(self, padding=(12, 10), style="Panel.TFrame")
        header.pack(fill="x", padx=10, pady=(8, 6))
        ttk.Label(header, text="Knight's Tour Game", style="Header.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            header,
            text="Clean Play UI: use top controls, then click highlighted squares on board.",
            style="Sub.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(2, 0))
        ttk.Label(header, textvariable=self.score_banner_var, style="Score.TLabel").grid(row=2, column=0, sticky="w", pady=(8, 0))
        ttk.Label(header, textvariable=self.turn_banner_var, style="Sub.TLabel").grid(row=3, column=0, sticky="w", pady=(2, 0))

        cards = ttk.Frame(header, style="Panel.TFrame")
        cards.grid(row=0, column=1, rowspan=4, sticky="e", padx=(18, 0))
        self.player1_card = tk.Label(
            cards,
            textvariable=self.player1_card_var,
            justify="left",
            bg="#2a9d8f",
            fg="white",
            font=("Consolas", 11, "bold"),
            padx=12,
            pady=8,
            relief="flat",
        )
        self.player1_card.grid(row=0, column=0, padx=(0, 8))
        self.player2_card = tk.Label(
            cards,
            textvariable=self.player2_card_var,
            justify="left",
            bg="#6c757d",
            fg="white",
            font=("Consolas", 11, "bold"),
            padx=12,
            pady=8,
            relief="flat",
        )
        self.player2_card.grid(row=0, column=1)

        top_controls = ttk.Frame(self, padding=(10, 6), style="Panel.TFrame")
        top_controls.pack(fill="x", padx=10, pady=(0, 6))
        self.top_controls = top_controls

        settings = ttk.LabelFrame(top_controls, text="Settings")
        settings.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        ttk.Label(settings, text="Mode").grid(row=0, column=0, sticky="w", padx=(8, 4), pady=6)
        ttk.OptionMenu(settings, self.mode_var, self.mode_var.get(), MODE_SOLO, MODE_2P, MODE_SOLVER).grid(row=0, column=1, sticky="w", pady=6)
        ttk.Label(settings, text="Board").grid(row=0, column=2, sticky="w", padx=(12, 4), pady=6)
        ttk.OptionMenu(settings, self.size_var, self.size_var.get(), "8", "16").grid(row=0, column=3, sticky="w", pady=6)
        ttk.Label(settings, text="Turn(s)").grid(row=0, column=4, sticky="w", padx=(12, 4), pady=6)
        ttk.Entry(settings, textvariable=self.turn_seconds_var, width=6).grid(row=0, column=5, sticky="w", pady=6)
        ttk.Label(settings, text="Solver").grid(row=0, column=6, sticky="w", padx=(12, 4), pady=6)
        ttk.OptionMenu(settings, self.solver_var, self.solver_var.get(), "warnsdorff", "backtracking").grid(row=0, column=7, sticky="w", pady=6)

        players = ttk.LabelFrame(top_controls, text="Players")
        players.grid(row=0, column=1, sticky="ew", padx=(0, 10))
        ttk.Label(players, text="P1").grid(row=0, column=0, sticky="w", padx=(8, 4), pady=6)
        ttk.Entry(players, textvariable=self.player1_var, width=14).grid(row=0, column=1, sticky="w", pady=6)
        ttk.Label(players, text="P2").grid(row=0, column=2, sticky="w", padx=(8, 4), pady=6)
        ttk.Entry(players, textvariable=self.player2_var, width=14).grid(row=0, column=3, sticky="w", pady=6)
        ttk.Checkbutton(players, text="Save winner", variable=self.save_var).grid(row=0, column=4, sticky="w", padx=(10, 0), pady=6)

        actions = ttk.LabelFrame(top_controls, text="Actions")
        actions.grid(row=0, column=2, sticky="e")
        ttk.Button(actions, text="New Game", command=self._start_game).grid(row=0, column=0, padx=4, pady=6)
        ttk.Button(actions, text="Undo", command=self._undo_move).grid(row=0, column=1, padx=4, pady=6)
        ttk.Button(actions, text="Hints", command=self._show_hints).grid(row=0, column=2, padx=4, pady=6)
        self.solve_button = ttk.Button(actions, text="Run Solver", command=self._solve_tour)
        self.solve_button.grid(row=0, column=3, padx=4, pady=6)
        ttk.Button(actions, text="Rules", command=self._show_rules).grid(row=0, column=4, padx=4, pady=6)
        ttk.Button(actions, text="Winners", command=self._show_winners).grid(row=0, column=5, padx=4, pady=6)
        self.toggle_controls_button = ttk.Button(actions, text="Hide Panels", command=self._toggle_controls_panel)
        self.toggle_controls_button.grid(row=0, column=6, padx=4, pady=6)

        aux = ttk.Frame(top_controls, style="Panel.TFrame")
        aux.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(8, 0))
        ttk.Label(aux, text="Node limit").grid(row=0, column=0, sticky="w")
        ttk.Entry(aux, textvariable=self.node_limit_var, width=12).grid(row=0, column=1, sticky="w", padx=(4, 10))
        ttk.Label(aux, text="Start row").grid(row=0, column=2, sticky="w")
        ttk.Entry(aux, textvariable=self.start_row_var, width=6).grid(row=0, column=3, sticky="w", padx=(4, 10))
        ttk.Label(aux, text="Start col").grid(row=0, column=4, sticky="w")
        ttk.Entry(aux, textvariable=self.start_col_var, width=6).grid(row=0, column=5, sticky="w", padx=(4, 10))
        ttk.Checkbutton(aux, text="Animate solver", variable=self.animate_var).grid(row=0, column=6, sticky="w")
        ttk.Label(aux, text="Speed").grid(row=0, column=7, sticky="w", padx=(10, 4))
        ttk.Scale(aux, from_=5, to=120, variable=self.speed_var, orient="horizontal", length=130).grid(row=0, column=8, sticky="w")
        ttk.Button(aux, text="Toggle Full Screen (F11)", command=self._toggle_fullscreen).grid(row=0, column=9, padx=(10, 0), sticky="w")

        self.progress = ttk.Progressbar(aux, mode="indeterminate", length=140)
        self.progress.grid(row=0, column=10, padx=(10, 0), sticky="w")

        board_wrap = ttk.Frame(self, style="Panel.TFrame", padding=8)
        board_wrap.pack(fill="both", expand=True, padx=10, pady=(0, 6))
        board_wrap.rowconfigure(0, weight=1)
        board_wrap.columnconfigure(0, weight=1)
        self.board_wrap = board_wrap

        self.canvas = tk.Canvas(board_wrap, bg="#fdfaf2", highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.canvas.bind("<Configure>", self._on_canvas_resize)
        self.canvas.bind("<Button-1>", self._on_canvas_click)

        output_wrap = ttk.Frame(self, style="Panel.TFrame", padding=(10, 6))
        output_wrap.pack(fill="x", padx=10, pady=(0, 4))
        self.output_wrap = output_wrap
        self.summary_label = ttk.Label(
            output_wrap,
            text="Output:\nMode: Solo Game\nPress New Game to begin.",
            style="Sub.TLabel",
            justify="left",
        )
        self.summary_label.pack(anchor="w")

        footer = ttk.Frame(self, padding=(10, 0, 10, 8))
        footer.pack(fill="x")
        self.footer = footer
        ttk.Label(footer, textvariable=self.status_var, style="Status.TLabel").pack(anchor="w")

    def _add_labeled_entry(self, parent: ttk.Frame, text: str, variable: tk.StringVar, row: int) -> None:
        ttk.Label(parent, text=text).grid(row=row, column=0, sticky="w", pady=(4, 0))
        ttk.Entry(parent, textvariable=variable, width=28).grid(row=row, column=0, sticky="ew", pady=(1, 4))

    def _add_labeled_option(self, parent: ttk.Frame, text: str, variable: tk.StringVar, options: list[str], row: int) -> None:
        ttk.Label(parent, text=text).grid(row=row, column=0, sticky="w", pady=(4, 0))
        ttk.OptionMenu(parent, variable, variable.get(), *options).grid(row=row, column=0, sticky="ew", pady=(1, 4))

    def _on_canvas_resize(self, _event: tk.Event) -> None:
        self._draw_board(self.current_size, self.current_path, self.hint_positions)

    def _on_canvas_click(self, event: tk.Event) -> None:
        if self.solving:
            return

        metrics = self._board_metrics
        if metrics is None:
            return

        side, cell, offset_x, offset_y, board_size = metrics
        if not (offset_x <= event.x <= offset_x + side and offset_y <= event.y <= offset_y + side):
            return

        col = int((event.x - offset_x) / cell)
        row = int((event.y - offset_y) / cell)

        if self.game_active and not self.game_finished:
            self._play_move(Position(row, col))
            return

        if board_size != int(self.size_var.get()):
            return

        self.start_row_var.set(str(row))
        self.start_col_var.set(str(col))
        self.current_start = Position(row, col)
        self.current_path = []
        self.hint_positions = []
        self._draw_board(board_size, [], [])
        self.status_var.set(f"Start position set to row {row}, col {col}.")

    def _parse_inputs(self) -> tuple[int, Position, int] | None:
        try:
            size = int(self.size_var.get())
            start_row = int(self.start_row_var.get())
            start_col = int(self.start_col_var.get())
            node_limit = int(self.node_limit_var.get())
        except ValueError:
            messagebox.showerror("Invalid input", "Size, start row, start col, and node limit must be integers.")
            return None

        if size not in (8, 16):
            messagebox.showerror("Invalid board", "Board size must be 8 or 16.")
            return None

        if not (0 <= start_row < size and 0 <= start_col < size):
            messagebox.showerror("Invalid start", f"Start coordinates must be in range 0..{size - 1}.")
            return None

        if node_limit < 1:
            messagebox.showerror("Invalid node limit", "Node limit must be a positive integer.")
            return None

        return size, Position(start_row, start_col), node_limit

    def _start_game(self) -> None:
        if self.solving:
            return

        parsed = self._parse_inputs()
        if parsed is None:
            return

        size, _start, _ = parsed
        mode = self.mode_var.get()
        if mode == MODE_SOLVER:
            messagebox.showinfo("Mode", "Change mode to Solo Game or Two Player Game to play manually.")
            return

        turn_seconds = self._parse_turn_seconds()
        if turn_seconds is None:
            return

        # Requirement: each game round starts from a random board position.
        start = Position(random.randint(0, size - 1), random.randint(0, size - 1))
        self.start_row_var.set(str(start.row))
        self.start_col_var.set(str(start.col))

        self._stop_animation()
        self._stop_turn_timer()
        self.game_active = True
        self.game_finished = False
        self.current_size = size
        self.current_start = start
        self.game_path = [start]
        self.game_visited = {start.key()}
        self.current_path = list(self.game_path)
        self.turn = 1
        self.last_mover = 0
        self.p1_score = 0
        self.p2_score = 0
        self.solo_lives = 3
        self.game_owner = {}
        self.bonus_cells = self._generate_bonus_cells(size, start)
        self.bonus_claimed = set()
        self.hint_positions = self._valid_game_moves(start)
        self._draw_board(size, self.current_path, self.hint_positions)
        self._update_game_output()
        self.time_left = turn_seconds
        self._start_turn_timer()
        self.status_var.set(
            f"Game started from random start ({start.row}, {start.col}). Click a highlighted legal move."
        )

    def _parse_turn_seconds(self) -> int | None:
        try:
            seconds = int(self.turn_seconds_var.get())
        except ValueError:
            messagebox.showerror("Invalid turn timer", "Turn seconds must be an integer (5 to 120).")
            return None

        if not (5 <= seconds <= 120):
            messagebox.showerror("Invalid turn timer", "Turn seconds must be between 5 and 120.")
            return None
        return seconds

    def _generate_bonus_cells(self, size: int, start: Position) -> set[str]:
        cells = [f"{r},{c}" for r in range(size) for c in range(size)]
        start_key = start.key()
        pool = [k for k in cells if k != start_key]
        random.shuffle(pool)
        bonus_count = max(4, min(size, len(pool) // 6))
        return set(pool[:bonus_count])

    def _start_turn_timer(self) -> None:
        self._stop_turn_timer()
        if not self.game_active or self.game_finished:
            return
        self.timer_job = self.after(1000, self._tick_timer)

    def _tick_timer(self) -> None:
        if not self.game_active or self.game_finished:
            return

        self.time_left = max(0, self.time_left - 1)
        self._update_game_output()
        if self.time_left == 0:
            self._handle_turn_timeout()
            return
        self.timer_job = self.after(1000, self._tick_timer)

    def _stop_turn_timer(self) -> None:
        if self.timer_job is not None:
            self.after_cancel(self.timer_job)
            self.timer_job = None

    def _reset_turn_time(self) -> None:
        seconds = self._parse_turn_seconds()
        if seconds is None:
            seconds = 20
        self.time_left = seconds
        self._start_turn_timer()

    def _handle_turn_timeout(self) -> None:
        if not self.game_active or self.game_finished:
            return

        if self.mode_var.get() == MODE_SOLO:
            self.solo_lives -= 1
            if self.solo_lives <= 0:
                self.status_var.set("Time out. No lives left.")
                self._finish_game(completed=False)
                return
            self.status_var.set(f"Time out. Lives left: {self.solo_lives}.")
            self._reset_turn_time()
            self._update_game_output()
            return

        penalty_target = self.turn
        if penalty_target == 1:
            self.p1_score = max(0, self.p1_score - 1)
        else:
            self.p2_score = max(0, self.p2_score - 1)

        self.turn = 2 if self.turn == 1 else 1
        self.status_var.set("Turn timed out. -1 point penalty and turn switched.")
        self._reset_turn_time()
        self._update_game_output()

    def _valid_game_moves(self, current: Position) -> list[Position]:
        return get_possible_moves(self.current_size, current.row, current.col, self.game_visited)

    def _show_hints(self) -> None:
        if not self.game_active or self.game_finished:
            messagebox.showinfo("Hints", "Start a game first.")
            return

        self.hint_positions = self._valid_game_moves(self.game_path[-1])
        self._draw_board(self.current_size, self.current_path, self.hint_positions)
        self.status_var.set(f"Showing {len(self.hint_positions)} legal moves.")

    def _undo_move(self) -> None:
        if not self.game_active or self.game_finished:
            self.status_var.set("Undo is available only while a game is active.")
            return

        if len(self.game_path) <= 1:
            self.status_var.set("Cannot undo start square.")
            return

        removed = self.game_path.pop()
        self.game_visited.remove(removed.key())
        owner = self.game_owner.pop(removed.key(), 0)
        if removed.key() in self.bonus_claimed:
            self.bonus_claimed.remove(removed.key())
            self.bonus_cells.add(removed.key())
            if owner == 1:
                self.p1_score = max(0, self.p1_score - self.bonus_value)
            elif owner == 2:
                self.p2_score = max(0, self.p2_score - self.bonus_value)

        if owner == 1:
            self.p1_score = max(0, self.p1_score - 1)
        elif owner == 2:
            self.p2_score = max(0, self.p2_score - 1)

        if self.mode_var.get() == MODE_2P:
            self.turn = owner if owner in (1, 2) else self.turn

        self.current_path = list(self.game_path)
        self.hint_positions = self._valid_game_moves(self.game_path[-1])
        self._draw_board(self.current_size, self.current_path, self.hint_positions)
        self._update_game_output()
        self._reset_turn_time()
        self.status_var.set("Last move undone.")

    def _play_move(self, target: Position) -> None:
        legal = self._valid_game_moves(self.game_path[-1])
        legal_keys = {p.key() for p in legal}
        if target.key() not in legal_keys:
            self._handle_illegal_move()
            return

        self.game_path.append(target)
        self.game_visited.add(target.key())
        self.game_owner[target.key()] = self.turn
        self.last_mover = self.turn
        if self.turn == 1:
            self.p1_score += 1
        elif self.turn == 2:
            self.p2_score += 1

        target_key = target.key()
        if target_key in self.bonus_cells:
            self.bonus_cells.remove(target_key)
            self.bonus_claimed.add(target_key)
            if self.turn == 1:
                self.p1_score += self.bonus_value
            else:
                self.p2_score += self.bonus_value

        self.current_path = list(self.game_path)
        self.hint_positions = self._valid_game_moves(target)

        total = self.current_size * self.current_size
        visited = len(self.game_path)

        if visited == total:
            self._finish_game(completed=True)
            return

        if not self.hint_positions:
            self._finish_game(completed=False)
            return

        if self.mode_var.get() == MODE_2P:
            self.turn = 2 if self.turn == 1 else 1

        self._reset_turn_time()
        self._draw_board(self.current_size, self.current_path, self.hint_positions)
        self._update_game_output()
        self.status_var.set(f"Move accepted. Visited {visited}/{total} squares.")

    def _handle_illegal_move(self) -> None:
        if self.mode_var.get() == MODE_SOLO:
            self.solo_lives -= 1
            if self.solo_lives <= 0:
                self.status_var.set("Illegal move. No lives left.")
                self._finish_game(completed=False)
                return
            self.status_var.set(f"Illegal move. Lives left: {self.solo_lives}.")
            self._update_game_output()
            return

        if self.turn == 1:
            self.p1_score = max(0, self.p1_score - 1)
        else:
            self.p2_score = max(0, self.p2_score - 1)
        self.turn = 2 if self.turn == 1 else 1
        self.status_var.set("Illegal move. -1 point penalty and turn switched.")
        self._reset_turn_time()
        self._update_game_output()

    def _finish_game(self, completed: bool) -> None:
        self._stop_turn_timer()
        self.game_finished = True
        self.game_active = False
        self._draw_board(self.current_size, self.current_path, [])

        if self.mode_var.get() == MODE_SOLO:
            total = self.current_size * self.current_size
            visited = len(self.current_path)
            if completed:
                self.status_var.set("You won. Full knight's tour completed.")
                self.summary_label.configure(text=f"Output:\nSolo Result: WIN\nVisited: {visited}/{total}")
                self._save_winner_record(self.player1_var.get().strip() or "Player 1")
                messagebox.showinfo("Victory", "Great job. You completed the full tour.")
            else:
                self.status_var.set("No legal moves left. Game over.")
                self.summary_label.configure(text=f"Output:\nSolo Result: Game Over\nVisited: {visited}/{total}")
                messagebox.showinfo("Game Over", f"No moves left. You reached {visited}/{total} squares.")
            return

        p1 = self.player1_var.get().strip() or "Player 1"
        p2 = self.player2_var.get().strip() or "Player 2"
        winner, winner_rule = self._determine_two_player_winner(p1, p2)

        result = "Completed Board" if completed else "No Moves Left"
        self.summary_label.configure(
            text=(
                "Output:\n"
                f"Two-Player Result: {result}\n"
                f"{p1}: {self.p1_score} | {p2}: {self.p2_score}\n"
                f"Winner: {winner}\n"
                f"Rule: {winner_rule}"
            )
        )
        self.status_var.set(f"Two-player game finished. Winner: {winner}.")

        if winner != "Draw":
            self._save_winner_record(winner)
        messagebox.showinfo(
            "Match Finished",
            f"{p1}: {self.p1_score}\n{p2}: {self.p2_score}\nWinner: {winner}\nRule: {winner_rule}",
        )

    def _determine_two_player_winner(self, p1: str, p2: str) -> tuple[str, str]:
        if self.p1_score > self.p2_score:
            return p1, "Higher score"
        if self.p2_score > self.p1_score:
            return p2, "Higher score"

        if self.last_mover == 1:
            return p1, "Tie on score, last legal move wins"
        if self.last_mover == 2:
            return p2, "Tie on score, last legal move wins"
        return "Draw", "Scores tied and no tie-break move"

    def _save_winner_record(self, winner_name: str) -> None:
        if not self.save_var.get():
            return

        save_winner(
            {
                "player": winner_name,
                "size": self.current_size,
                "start": self.current_start.label(),
                "pathLength": len(self.current_path),
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "sequence": [f"{p.row + 1},{p.col + 1}" for p in self.current_path],
            }
        )

    def _update_game_output(self) -> None:
        mode = self.mode_var.get()
        total = self.current_size * self.current_size
        visited = len(self.current_path)
        p1 = self.player1_var.get().strip() or "Player 1"
        p2 = self.player2_var.get().strip() or "Player 2"

        self.score_banner_var.set(f"Score: {p1} {self.p1_score} | {p2} {self.p2_score}")

        if mode == MODE_SOLO:
            self.player1_card_var.set(f"{p1}\nScore: {self.p1_score}\nLives: {self.solo_lives}")
            self.player2_card_var.set("Single Player\nInactive")
            self.player1_card.configure(bg="#2a9d8f")
            self.player2_card.configure(bg="#6c757d")
            self.turn_banner_var.set(f"Mode: Solo | Time Left: {self.time_left}s | Lives: {self.solo_lives}")
            self.summary_label.configure(
                text=(
                    "Output:\n"
                    "Mode: Solo Game\n"
                    f"Visited: {visited}/{total}\n"
                    f"Available moves: {len(self.hint_positions)}\n"
                    f"Lives: {self.solo_lives}\n"
                    f"Time Left: {self.time_left}s\n"
                    f"Bonus left: {len(self.bonus_cells)}"
                )
            )
            return

        if mode == MODE_SOLVER:
            self.player1_card_var.set(f"{p1}\nSolver")
            self.player2_card_var.set("No Opponent")
            self.player1_card.configure(bg="#264653")
            self.player2_card.configure(bg="#6c757d")
            self.turn_banner_var.set("Mode: Solver | Time Left: - | Lives: -")
            self.summary_label.configure(
                text=(
                    "Output:\n"
                    "Mode: Solver\n"
                    "Press Run Solver to generate an automatic tour."
                )
            )
            return

        turn_name = p1 if self.turn == 1 else p2
        self.player1_card_var.set(f"{p1}\nScore: {self.p1_score}")
        self.player2_card_var.set(f"{p2}\nScore: {self.p2_score}")
        self.player1_card.configure(bg="#2a9d8f" if self.turn == 1 else "#6c757d")
        self.player2_card.configure(bg="#e76f51" if self.turn == 2 else "#6c757d")
        self.turn_banner_var.set(f"Mode: Two-Player | Turn: {turn_name} | Time Left: {self.time_left}s")
        self.summary_label.configure(
            text=(
                "Output:\n"
                "Mode: Two-Player\n"
                f"Turn: {turn_name}\n"
                f"{p1}: {self.p1_score} | {p2}: {self.p2_score}\n"
                f"Visited: {visited}/{total}\n"
                f"Available moves: {len(self.hint_positions)}\n"
                f"Time Left: {self.time_left}s\n"
                f"Bonus left: {len(self.bonus_cells)}"
            )
        )

    def _solve_tour(self) -> None:
        if self.solving:
            return

        if self.mode_var.get() != MODE_SOLVER:
            messagebox.showinfo("Mode", "Set mode to solver before running automatic solve.")
            return

        parsed = self._parse_inputs()
        if parsed is None:
            return

        size, start, node_limit = parsed
        solver = self.solver_var.get()

        self._stop_animation()
        self.solving = True
        self.solve_button.configure(state="disabled")
        self.progress.start(10)
        self.status_var.set("Solving... backtracking can take longer on large boards.")
        self.update_idletasks()

        worker = threading.Thread(
            target=self._solve_worker,
            args=(size, start, node_limit, solver),
            daemon=True,
        )
        worker.start()

    def _solve_worker(self, size: int, start: Position, node_limit: int, solver: str) -> None:
        if solver == "warnsdorff":
            path = solve_warnsdorff(size, start)
        else:
            path = solve_backtracking(size, start, node_limit)
        report = validate_path(size, path, start) if path else None
        self.after(0, lambda: self._on_solve_complete(size, start, path, report))

    def _on_solve_complete(self, size: int, start: Position, path: list[Position] | None, report: object | None) -> None:
        self.solving = False
        self.progress.stop()
        self.solve_button.configure(state="normal")
        self.current_size = size
        self.current_start = start

        self.game_active = False
        self.game_finished = False
        self.game_path = []
        self.game_visited = set()
        self.game_owner = {}
        self.bonus_cells = set()
        self.bonus_claimed = set()
        self.hint_positions = []

        if not path:
            self.current_path = []
            self._draw_board(size, [], [])
            self.summary_label.configure(text="Output:\nSolver: No complete tour found.")
            self.status_var.set("No complete tour found with current settings.")
            return

        self.current_path = path
        self.summary_label.configure(
            text=(
                "Output:\n"
                f"Solver valid: {report.valid}\n"
                f"Reason: {report.reason}\n"
                f"Coverage: {report.coverage:.2%}\n"
                f"Moves: {len(path)}"
            )
        )

        if report.valid and self.save_var.get():
            self._save_winner_record(self.player1_var.get().strip() or "Solver")
            self.status_var.set("Solved and winner saved.")
        else:
            self.status_var.set("Solved successfully.")

        if self.animate_var.get():
            self._start_animation()
        else:
            self._draw_board(size, path, [])

    def _start_animation(self) -> None:
        self._stop_animation()
        self.animation_index = 1
        self._animate_step()

    def _animate_step(self) -> None:
        if not self.current_path:
            return

        show = self.current_path[: self.animation_index]
        self._draw_board(self.current_size, show, [])
        self.animation_index += 1

        if self.animation_index <= len(self.current_path):
            delay_ms = max(5, int(130 - self.speed_var.get()))
            self.animation_job = self.after(delay_ms, self._animate_step)
        else:
            self.animation_job = None

    def _stop_animation(self) -> None:
        if self.animation_job is not None:
            self.after_cancel(self.animation_job)
            self.animation_job = None

    def _random_start(self) -> None:
        if self.solving:
            return

        size = int(self.size_var.get())
        row = random.randint(0, size - 1)
        col = random.randint(0, size - 1)
        self.start_row_var.set(str(row))
        self.start_col_var.set(str(col))
        self.current_start = Position(row, col)
        self.current_path = []
        self.hint_positions = []
        self._draw_board(size, [], [])
        self.status_var.set(f"Random start selected: row {row}, col {col}.")

    def _clear_board(self) -> None:
        if self.solving:
            return

        self._stop_animation()
        self._stop_turn_timer()
        size = int(self.size_var.get())
        self.current_path = []
        self.hint_positions = []
        self.game_active = False
        self.game_finished = False
        self.game_path = []
        self.game_visited = set()
        self.game_owner = {}
        self.p1_score = 0
        self.p2_score = 0
        self.turn = 1
        self.last_mover = 0
        self.solo_lives = 3
        self.time_left = 0
        self.bonus_cells = set()
        self.bonus_claimed = set()

        try:
            self.current_start = Position(int(self.start_row_var.get()), int(self.start_col_var.get()))
        except ValueError:
            self.current_start = Position(0, 0)

        self._draw_board(size, [], [])
        self.summary_label.configure(text="Output:\nBoard cleared. Start a new game or run solver.")
        self.status_var.set("Board cleared.")

    def _draw_board(self, size: int, path: list[Position], hints: list[Position]) -> None:
        self.canvas.delete("all")
        self.current_size = size

        # Use real canvas size so the board never gets clipped off-screen.
        canvas_w = max(self.canvas.winfo_width(), 240)
        canvas_h = max(self.canvas.winfo_height(), 240)
        side = max(120, min(canvas_w, canvas_h) - 36)
        cell = side / size
        offset_x = (canvas_w - side) / 2
        offset_y = (canvas_h - side) / 2
        self._board_metrics = (side, cell, offset_x, offset_y, size)

        light = "#f7e8ca"
        dark = "#bb8f63"
        p1_color = "#2a9d8f"
        p2_color = "#e76f51"

        for row in range(size):
            for col in range(size):
                x1 = offset_x + col * cell
                y1 = offset_y + row * cell
                x2 = x1 + cell
                y2 = y1 + cell
                color = light if (row + col) % 2 == 0 else dark
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="#6e5a44")

        for hint in hints:
            x1 = offset_x + hint.col * cell
            y1 = offset_y + hint.row * cell
            x2 = x1 + cell
            y2 = y1 + cell
            self.canvas.create_rectangle(x1, y1, x2, y2, outline="#1f6f8b", width=3)

        for bonus_key in self.bonus_cells:
            row_s, col_s = bonus_key.split(",")
            row = int(row_s)
            col = int(col_s)
            if bonus_key in self.game_visited:
                continue
            cx = offset_x + (col + 0.5) * cell
            cy = offset_y + (row + 0.5) * cell
            self.canvas.create_text(
                cx,
                cy,
                text="+",
                fill="#d1495b",
                font=("Consolas", max(9, int(cell * 0.28)), "bold"),
            )

        for index in range(size):
            x = offset_x + (index + 0.5) * cell
            y = offset_y + (index + 0.5) * cell
            font_size = max(7, int(cell * 0.2))
            self.canvas.create_text(x, offset_y - 10, text=str(index), fill="#5a4737", font=("Consolas", font_size))
            self.canvas.create_text(offset_x - 12, y, text=str(index), fill="#5a4737", font=("Consolas", font_size))

        if not path:
            if 0 <= self.current_start.row < size and 0 <= self.current_start.col < size:
                cx = offset_x + (self.current_start.col + 0.5) * cell
                cy = offset_y + (self.current_start.row + 0.5) * cell
                r = max(6, cell * 0.18)
                self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill=p1_color, outline="")
                self.canvas.create_text(
                    cx,
                    cy,
                    text="S",
                    fill="white",
                    font=("Consolas", max(8, int(cell * 0.25)), "bold"),
                )
            return

        centers: list[tuple[float, float]] = []
        move_number = {position.key(): index + 1 for index, position in enumerate(path)}

        for square in path:
            cx = offset_x + (square.col + 0.5) * cell
            cy = offset_y + (square.row + 0.5) * cell
            centers.append((cx, cy))

        for index in range(len(centers) - 1):
            x1, y1 = centers[index]
            x2, y2 = centers[index + 1]
            self.canvas.create_line(x1, y1, x2, y2, fill="#143d59", width=2)

        if self.mode_var.get() == MODE_2P:
            for pos in path[1:]:
                owner = self.game_owner.get(pos.key(), 0)
                if owner not in (1, 2):
                    continue
                color = p1_color if owner == 1 else p2_color
                cx = offset_x + (pos.col + 0.5) * cell
                cy = offset_y + (pos.row + 0.5) * cell
                r = max(3, cell * 0.11)
                self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill=color, outline="")

        if size <= 8:
            for position in path:
                cx = offset_x + (position.col + 0.5) * cell
                cy = offset_y + (position.row + 0.5) * cell
                num = move_number[position.key()]
                self.canvas.create_text(
                    cx,
                    cy,
                    text=str(num),
                    fill="#1f1f1f",
                    font=("Consolas", max(7, int(cell * 0.23)), "bold"),
                )

        first_x, first_y = centers[0]
        last_x, last_y = centers[-1]
        radius = max(5, cell * 0.17)
        self.canvas.create_oval(first_x - radius, first_y - radius, first_x + radius, first_y + radius, fill=p1_color, outline="")
        self.canvas.create_oval(last_x - radius, last_y - radius, last_x + radius, last_y + radius, fill="#264653", outline="")
        self.canvas.create_text(first_x, first_y, text="S", fill="white", font=("Consolas", max(8, int(cell * 0.2)), "bold"))
        self.canvas.create_text(last_x, last_y, text="K", fill="white", font=("Consolas", max(8, int(cell * 0.2)), "bold"))

    def _show_rules(self) -> None:
        messagebox.showinfo(
            "Game Rules",
            "Solo Game:\n"
            "- Start from selected square.\n"
            "- Move like a knight (L-shape).\n"
            "- Visit all squares once to win.\n\n"
            "Two Player Game:\n"
            "- Players alternate legal knight moves on one shared path.\n"
            "- Each move adds 1 point for the current player.\n"
            "- Bonus squares (+) add extra points.\n"
            "- Illegal move: -1 point and turn switches.\n"
            "- Timer expiry: -1 point and turn switches.\n"
            "- When no legal moves remain or board is complete, game ends.\n"
            "- Winner is higher score. If tied, last legal mover wins.\n\n"
            "Solo Game extras:\n"
            "- You have 3 lives. Illegal move or timeout loses a life.\n"
            "- Lose all lives and game ends.\n\n"
            "Tip: Use Show Hints to see legal squares.",
        )

    def _show_winners(self) -> None:
        winners = get_winners()
        if not winners:
            messagebox.showinfo("Winners", "No winner records yet.")
            return

        lines = []
        for index, row in enumerate(winners[:10], start=1):
            lines.append(
                f"{index}. {row.get('player', 'Anonymous')} | {row.get('size', '?')}x{row.get('size', '?')}"
                f" | start {row.get('start', '?')} | {row.get('timestamp', '?')}"
            )
        messagebox.showinfo("Recent Winners", "\n".join(lines))


def main() -> int:
    app = KnightTourGUI()
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
