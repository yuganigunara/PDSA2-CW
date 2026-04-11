from __future__ import annotations

import queue
import random
import threading
import tkinter as tk
from tkinter import messagebox, ttk

from snake_ladder.algorithms import timed_bfs, timed_dp
from snake_ladder.board import (
    MAX_BOARD_SIZE,
    MIN_BOARD_SIZE,
    ValidationError,
    generate_random_board,
    validate_board_size,
)
from snake_ladder.database import DatabaseError, ResultRepository
from snake_ladder.queens import (
    QUEENS_BOARD_SIZE,
    QUEENS_KNOWN_MAX_SOLUTIONS,
    QueensValidationError,
    benchmark_sixteen_queens,
    compare_speed_text,
    find_one_solution,
    validate_numeric_answer,
    validate_player_name,
)


class SnakeAndLadderGUI:
    def __init__(self, repository: ResultRepository | None = None) -> None:
        self.repository = repository or ResultRepository()

        self.board = None
        self.correct_answer: int | None = None
        self.bfs_time_ns = 0
        self.dp_time_ns = 0

        self.root = tk.Tk()
        self.root.title("Snake and Ladder Coursework")
        self.root.geometry("1200x900")
        self.root.minsize(1000, 760)

        self.player_name_var = tk.StringVar()
        self.board_size_var = tk.StringVar(value="6")
        self.selected_option = tk.IntVar(value=-1)

        self.option_buttons: list[ttk.Radiobutton] = []
        self.canvas_size = 780
        self.queens_window: tk.Toplevel | None = None
        self.queens_player_var = tk.StringVar()
        self.queens_answer_var = tk.StringVar()
        self.queens_result_var = tk.StringVar(value="Run benchmark to start.")
        self.queens_benchmark = None
        self.queens_benchmark_running = False
        self.queens_result_queue: queue.Queue[tuple[str, object]] = queue.Queue()
        self.run_queens_button: ttk.Button | None = None
        self.load_queens_button: ttk.Button | None = None
        self.queens_canvas: tk.Canvas | None = None
        self.queens_canvas_size = 560
        self.queens_positions: tuple[int, ...] | None = None
        self.queens_progress: ttk.Progressbar | None = None
        self.submit_queens_button: ttk.Button | None = None

        self._build_layout()

    def _build_layout(self) -> None:
        main = ttk.Frame(self.root, padding=16)
        main.pack(fill=tk.BOTH, expand=True)

        title = ttk.Label(
            main,
            text="Snake and Ladder: Minimum Dice Throw Challenge",
            font=("Segoe UI", 16, "bold"),
        )
        title.pack(anchor=tk.W, pady=(0, 12))

        controls = ttk.LabelFrame(main, text="Round Setup", padding=12)
        controls.pack(fill=tk.X)

        ttk.Label(controls, text="Player Name:").grid(row=0, column=0, sticky=tk.W, padx=(0, 8))
        name_entry = ttk.Entry(controls, textvariable=self.player_name_var, width=24)
        name_entry.grid(row=0, column=1, sticky=tk.W, padx=(0, 12))

        ttk.Label(controls, text=f"Board Size N ({MIN_BOARD_SIZE}-{MAX_BOARD_SIZE}):").grid(
            row=0, column=2, sticky=tk.W, padx=(0, 8)
        )
        size_spin = ttk.Spinbox(
            controls,
            from_=MIN_BOARD_SIZE,
            to=MAX_BOARD_SIZE,
            textvariable=self.board_size_var,
            width=6,
        )
        size_spin.grid(row=0, column=3, sticky=tk.W, padx=(0, 12))

        self.start_button = ttk.Button(
            controls,
            text="Start New Round",
            command=self.start_round,
        )
        self.start_button.grid(row=0, column=4, sticky=tk.E)

        queens_row = ttk.Frame(main)
        queens_row.pack(fill=tk.X, pady=(10, 0))

        self.queens_button = ttk.Button(
            queens_row,
            text="Open Sixteen Queens Puzzle GUI",
            command=self.open_queens_window,
        )
        self.queens_button.pack(anchor=tk.W)

        body = ttk.Frame(main)
        body.pack(fill=tk.BOTH, expand=True, pady=(12, 12))

        board_frame = ttk.LabelFrame(body, text="Generated Board", padding=12)
        board_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        self.board_canvas = tk.Canvas(
            board_frame,
            width=self.canvas_size,
            height=self.canvas_size,
            bg="#f8fafc",
            highlightthickness=1,
            highlightbackground="#d1d5db",
        )
        self.board_canvas.pack(fill=tk.BOTH, expand=True)
        self.board_canvas.bind("<Configure>", self._on_canvas_resize)

        side_panel = ttk.LabelFrame(body, text="Answer Panel", padding=12)
        side_panel.pack(side=tk.RIGHT, fill=tk.Y)

        question_frame = ttk.LabelFrame(side_panel, text="Question", padding=12)
        question_frame.pack(fill=tk.BOTH, expand=True)

        self.question_label = ttk.Label(
            question_frame,
            text="Press 'Start New Round' to generate snakes/ladders and answer options.",
            wraplength=300,
        )
        self.question_label.pack(anchor=tk.W, pady=(0, 8))

        options_title = ttk.Label(
            question_frame,
            text="Choose one answer:",
            font=("Segoe UI", 10, "bold"),
        )
        options_title.pack(anchor=tk.W, pady=(0, 6))

        self.options_container = ttk.Frame(question_frame)
        self.options_container.pack(anchor=tk.W, fill=tk.X)

        submit_row = ttk.Frame(question_frame)
        submit_row.pack(fill=tk.X, pady=(10, 0))

        self.submit_button = ttk.Button(
            submit_row,
            text="Submit Answer",
            command=self.submit_answer,
            state=tk.DISABLED,
        )
        self.submit_button.pack(side=tk.LEFT)

        self.status_label = ttk.Label(side_panel, text="Ready.", foreground="#1f2937", wraplength=300)
        self.status_label.pack(anchor=tk.W, fill=tk.X, pady=(10, 0))

    def start_round(self) -> None:
        try:
            self._read_player_name()
            board_size = self._read_board_size()

            self.board = generate_random_board(board_size)
            bfs_result = timed_bfs(self.board)
            dp_result = timed_dp(self.board)

            self.bfs_time_ns = bfs_result.time_ns
            self.dp_time_ns = dp_result.time_ns

            if bfs_result.minimum_throws != dp_result.minimum_throws:
                self.correct_answer = None
                self._clear_options()
                self._render_board_canvas()
                self.question_label.config(
                    text=(
                        "DRAW: BFS and DP gave different minimum throws. "
                        f"BFS={bfs_result.minimum_throws}, DP={dp_result.minimum_throws}."
                    )
                )
                self.submit_button.config(state=tk.DISABLED)
                self.status_label.config(
                    text=(
                        f"BFS time: {self.bfs_time_ns} ns | DP time: {self.dp_time_ns} ns"
                    )
                )
                return

            self.correct_answer = bfs_result.minimum_throws
            self._render_board_canvas()
            self._render_options(self._build_answer_options(self.correct_answer))
            self.question_label.config(
                text="What is the minimum number of dice throws needed to reach N^2?"
            )
            self.submit_button.config(state=tk.NORMAL)
            self.status_label.config(
                text=f"Round generated. BFS time: {self.bfs_time_ns} ns | DP time: {self.dp_time_ns} ns"
            )

        except ValidationError as exc:
            messagebox.showerror("Validation Error", str(exc), parent=self.root)
        except Exception as exc:  # Defensive fallback for GUI flows.
            messagebox.showerror("Unexpected Error", str(exc), parent=self.root)

    def submit_answer(self) -> None:
        if self.correct_answer is None:
            messagebox.showinfo("Draw", "This round is a draw; start a new round.", parent=self.root)
            return

        selected = self.selected_option.get()
        if selected == -1:
            messagebox.showwarning("Answer Needed", "Select one option first.", parent=self.root)
            return

        if selected == self.correct_answer:
            self.status_label.config(
                text=(
                    f"WIN. Correct answer: {self.correct_answer}. "
                    f"BFS: {self.bfs_time_ns} ns | DP: {self.dp_time_ns} ns"
                ),
                foreground="#065f46",
            )
            player_name = self.player_name_var.get().strip()
            try:
                if self.board is not None:
                    self.repository.save_correct_answer(
                        player_name=player_name,
                        answer=self.correct_answer,
                        bfs_time_ns=self.bfs_time_ns,
                        dp_time_ns=self.dp_time_ns,
                        board=self.board,
                    )
                    messagebox.showinfo(
                        "WIN",
                        "Correct answer! Result saved to database.",
                        parent=self.root,
                    )
            except DatabaseError as exc:
                messagebox.showwarning(
                    "Database Error",
                    f"Correct answer but could not save: {exc}",
                    parent=self.root,
                )
            self.submit_button.config(state=tk.DISABLED)
            return

        self.status_label.config(
            text=(
                f"LOSE. Your answer: {selected}. Correct: {self.correct_answer}. "
                f"BFS: {self.bfs_time_ns} ns | DP: {self.dp_time_ns} ns"
            ),
            foreground="#991b1b",
        )
        messagebox.showinfo(
            "LOSE",
            f"Incorrect answer. Correct answer is {self.correct_answer}.",
            parent=self.root,
        )
        self.submit_button.config(state=tk.DISABLED)

    def run(self) -> None:
        self.root.mainloop()

    def open_queens_window(self) -> None:
        if self.queens_window is not None and self.queens_window.winfo_exists():
            self.queens_window.lift()
            return

        self.queens_window = tk.Toplevel(self.root)
        self.queens_window.title("Sixteen Queens Puzzle")
        self.queens_window.geometry("1200x860")
        self.queens_window.minsize(1080, 760)
        self.queens_window.protocol("WM_DELETE_WINDOW", self._on_queens_window_close)

        frame = ttk.Frame(self.queens_window, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            frame,
            text="Sixteen Queens Puzzle",
            font=("Segoe UI", 18, "bold"),
        ).pack(anchor=tk.W, pady=(0, 8))

        ttk.Label(
            frame,
            text=(
                "Find the maximum number of solutions for placing 16 queens on 16x16 board. "
                "You can submit your answer even while benchmark is running."
            ),
            wraplength=1080,
        ).pack(anchor=tk.W, pady=(0, 10))

        top_controls = ttk.Frame(frame)
        top_controls.pack(fill=tk.X, pady=(0, 12))

        self.run_queens_button = ttk.Button(
            top_controls,
            text="Run Sequential + Threaded Benchmark",
            command=self.run_queens_benchmark,
        )
        self.run_queens_button.pack(side=tk.LEFT)

        self.load_queens_button = ttk.Button(
            top_controls,
            text="Use Latest Benchmark",
            command=self.load_latest_queens_benchmark,
        )
        self.load_queens_button.pack(side=tk.LEFT, padx=(10, 0))

        self.queens_progress = ttk.Progressbar(top_controls, mode="indeterminate", length=220)
        self.queens_progress.pack(side=tk.LEFT, padx=(16, 0))

        ttk.Label(
            frame,
            textvariable=self.queens_result_var,
            wraplength=1080,
            foreground="#1f2937",
        ).pack(anchor=tk.W, pady=(0, 12))

        body = ttk.Frame(frame)
        body.pack(fill=tk.BOTH, expand=True)

        left = ttk.Frame(body)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 14))

        board_box = ttk.LabelFrame(left, text="16x16 Queens Board (Graphical View)", padding=10)
        board_box.pack(fill=tk.BOTH, expand=True)

        self.queens_canvas = tk.Canvas(
            board_box,
            width=self.queens_canvas_size,
            height=self.queens_canvas_size,
            bg="#ffffff",
            highlightthickness=1,
            highlightbackground="#cbd5e1",
        )
        self.queens_canvas.pack(fill=tk.BOTH, expand=True)
        self.queens_canvas.bind("<Configure>", self._on_queens_canvas_resize)

        right = ttk.Frame(body)
        right.pack(side=tk.RIGHT, fill=tk.Y, padx=(6, 0))

        form = ttk.LabelFrame(right, text="Player Answer", padding=12)
        form.pack(fill=tk.X)

        ttk.Label(form, text="Player Name:").grid(row=0, column=0, sticky=tk.W, padx=(0, 8), pady=4)
        ttk.Entry(form, textvariable=self.queens_player_var, width=24).grid(
            row=0, column=1, sticky=tk.W, padx=(0, 12), pady=4
        )

        ttk.Label(form, text="Your Maximum Solution Guess:").grid(
            row=1, column=0, sticky=tk.W, padx=(0, 8), pady=4
        )
        ttk.Entry(form, textvariable=self.queens_answer_var, width=24).grid(
            row=1, column=1, sticky=tk.W, padx=(0, 12), pady=4
        )

        helper = ttk.Label(
            form,
            text="Submit your answer while or after benchmark execution.",
            wraplength=280,
            foreground="#334155",
        )
        helper.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=(6, 0))

        self.submit_queens_button = ttk.Button(form, text="Submit Answer", command=self.submit_queens_answer)
        self.submit_queens_button.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=(10, 0))

        if self.queens_positions is None:
            self.queens_positions = find_one_solution(QUEENS_BOARD_SIZE)
        self._render_queens_board()

    def load_latest_queens_benchmark(self) -> None:
        try:
            benchmark = self.repository.get_latest_queens_benchmark()
            if benchmark is None:
                self.queens_result_var.set("No benchmark found. Run the benchmark first.")
                self.queens_benchmark = None
                return

            self.queens_benchmark = benchmark
            self.queens_result_var.set(
                " | ".join(
                    [
                        f"Seq solutions: {benchmark.sequential_solutions}",
                        f"Seq time: {benchmark.sequential_time_ns} ns",
                        f"Thread solutions: {benchmark.threaded_solutions}",
                        f"Thread time: {benchmark.threaded_time_ns} ns",
                        compare_speed_text(benchmark),
                    ]
                )
            )
        except DatabaseError as exc:
            messagebox.showerror("Database Error", str(exc), parent=self.queens_window)

    def run_queens_benchmark(self) -> None:
        if self.queens_benchmark_running:
            return

        self.queens_benchmark_running = True
        self._set_queens_controls_enabled(False)
        self.queens_result_var.set("Running benchmark in background... please wait.")
        if self.queens_progress is not None:
            self.queens_progress.start(12)

        worker = threading.Thread(target=self._run_queens_benchmark_worker, daemon=True)
        worker.start()
        self.root.after(150, self._poll_queens_result_queue)

    def _run_queens_benchmark_worker(self) -> None:
        try:
            benchmark = benchmark_sixteen_queens()
            self.repository.save_queens_benchmark(benchmark)
            self.queens_result_queue.put(("ok", benchmark))
        except (DatabaseError, QueensValidationError) as exc:
            self.queens_result_queue.put(("err", str(exc)))

    def _poll_queens_result_queue(self) -> None:
        try:
            status, payload = self.queens_result_queue.get_nowait()
        except queue.Empty:
            if self.queens_benchmark_running:
                self.root.after(150, self._poll_queens_result_queue)
            return

        self.queens_benchmark_running = False
        self._set_queens_controls_enabled(True)
        if self.queens_progress is not None:
            self.queens_progress.stop()

        if status == "err":
            self.queens_result_var.set("Benchmark failed. Check error message.")
            if self.queens_window is not None and self.queens_window.winfo_exists():
                messagebox.showerror("Error", str(payload), parent=self.queens_window)
            else:
                messagebox.showerror("Error", str(payload), parent=self.root)
            return

        benchmark = payload
        self.queens_benchmark = benchmark
        self.queens_result_var.set(
            " | ".join(
                [
                    f"Seq solutions: {benchmark.sequential_solutions}",
                    f"Seq time: {benchmark.sequential_time_ns} ns",
                    f"Thread solutions: {benchmark.threaded_solutions}",
                    f"Thread time: {benchmark.threaded_time_ns} ns",
                    compare_speed_text(benchmark),
                ]
            )
        )

    def _set_queens_controls_enabled(self, enabled: bool) -> None:
        state = tk.NORMAL if enabled else tk.DISABLED
        if self.run_queens_button is not None:
            self.run_queens_button.config(state=state)
        if self.load_queens_button is not None:
            self.load_queens_button.config(state=state)

    def _on_queens_window_close(self) -> None:
        if self.queens_benchmark_running:
            messagebox.showinfo(
                "Benchmark Running",
                "Please wait for benchmark to finish before closing this window.",
                parent=self.queens_window,
            )
            return
        if self.queens_window is not None:
            self.queens_window.destroy()
            self.queens_window = None

    def _on_queens_canvas_resize(self, event: tk.Event) -> None:
        size = max(320, min(event.width, event.height) - 8)
        if size != self.queens_canvas_size:
            self.queens_canvas_size = size
            self._render_queens_board()

    def _render_queens_board(self) -> None:
        if self.queens_canvas is None:
            return

        self.queens_canvas.delete("all")
        n = QUEENS_BOARD_SIZE
        positions = self.queens_positions or find_one_solution(n)
        self.queens_positions = positions

        pad = 14
        board_px = self.queens_canvas_size
        step = (board_px - (2 * pad)) / n

        for row in range(n):
            for col in range(n):
                x1 = pad + (col * step)
                y1 = pad + (row * step)
                x2 = x1 + step
                y2 = y1 + step
                fill = "#f8fafc" if (row + col) % 2 == 0 else "#dbeafe"
                self.queens_canvas.create_rectangle(x1, y1, x2, y2, fill=fill, outline="#cbd5e1")

        for row, col in enumerate(positions):
            cx = pad + (col * step) + (step / 2)
            cy = pad + (row * step) + (step / 2)
            r = max(6.0, step * 0.26)
            self.queens_canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill="#0f172a", outline="")
            self.queens_canvas.create_text(
                cx,
                cy,
                text="Q",
                fill="#ffffff",
                font=("Segoe UI", max(7, int(step * 0.22)), "bold"),
            )

        self.queens_canvas.create_text(
            pad,
            4,
            anchor=tk.NW,
            text="One valid non-attacking 16-queens placement (sample)",
            fill="#1e3a8a",
            font=("Segoe UI", 11, "bold"),
        )

    def submit_queens_answer(self) -> None:
        try:
            player_name = validate_player_name(self.queens_player_var.get())
            answer = validate_numeric_answer(self.queens_answer_var.get())
            if self.queens_benchmark is not None:
                correct = self.queens_benchmark.sequential_solutions
            else:
                correct = QUEENS_KNOWN_MAX_SOLUTIONS

            if answer != correct:
                messagebox.showinfo(
                    "Incorrect",
                    f"Incorrect answer. Correct answer is {correct}.",
                    parent=self.queens_window,
                )
                return

            cycle_id = self.repository.get_current_queens_cycle()
            if self.repository.has_recognized_queens_answer(answer=answer, cycle_id=cycle_id):
                messagebox.showwarning(
                    "Already Recognized",
                    "This correct response is already recognized for this cycle. Try again later.",
                    parent=self.queens_window,
                )
                return

            self.repository.save_queens_correct_answer(
                player_name=player_name,
                answer=answer,
                cycle_id=cycle_id,
            )
            self.repository.reset_queens_recognition_cycle()
            messagebox.showinfo(
                "Correct",
                "Correct answer saved. Recognition cycle reset for future players.",
                parent=self.queens_window,
            )
        except (DatabaseError, QueensValidationError) as exc:
            messagebox.showerror("Error", str(exc), parent=self.queens_window)

    def _read_player_name(self) -> str:
        name = self.player_name_var.get().strip()
        if not name:
            raise ValidationError("Player name cannot be empty.")
        if len(name) > 50:
            raise ValidationError("Player name is too long.")
        return name

    def _read_board_size(self) -> int:
        raw = self.board_size_var.get().strip()
        if not raw.isdigit():
            raise ValidationError("Board size must be numeric.")
        size = int(raw)
        validate_board_size(size)
        return size

    def _build_answer_options(self, correct: int) -> list[int]:
        low = max(1, correct - 3)
        high = correct + 3

        options = {correct}
        while len(options) < 3:
            options.add(random.randint(low, high))

        shuffled = list(options)
        random.shuffle(shuffled)
        return shuffled

    def _on_canvas_resize(self, event: tk.Event) -> None:
        size = max(460, min(event.width, event.height) - 8)
        if size != self.canvas_size:
            self.canvas_size = size
            self._render_board_canvas()

    def _cell_center(self, cell: int, size: int, step: float, pad: float) -> tuple[float, float]:
        row_from_bottom = (cell - 1) // size
        col_in_row = (cell - 1) % size

        # Serpentine numbering: odd rows reverse direction.
        if row_from_bottom % 2 == 1:
            col = size - 1 - col_in_row
        else:
            col = col_in_row

        x = pad + (col * step) + (step / 2)
        y = pad + ((size - 1 - row_from_bottom) * step) + (step / 2)
        return x, y

    def _render_board_canvas(self) -> None:
        self.board_canvas.delete("all")
        if self.board is None:
            return

        size = self.board.size
        canvas_px = self.canvas_size
        pad = 18
        step = (canvas_px - (2 * pad)) / size

        # Draw cells and numbers.
        for cell in range(1, self.board.goal + 1):
            row_from_bottom = (cell - 1) // size
            col_in_row = (cell - 1) % size
            if row_from_bottom % 2 == 1:
                col = size - 1 - col_in_row
            else:
                col = col_in_row

            x1 = pad + (col * step)
            y1 = pad + ((size - 1 - row_from_bottom) * step)
            x2 = x1 + step
            y2 = y1 + step

            fill = "#eef2ff" if (row_from_bottom + col) % 2 == 0 else "#ffffff"
            self.board_canvas.create_rectangle(x1, y1, x2, y2, fill=fill, outline="#cbd5e1")
            self.board_canvas.create_text(
                x1 + 8,
                y1 + 8,
                text=str(cell),
                anchor=tk.NW,
                fill="#0f172a",
                font=("Segoe UI", 8, "bold"),
            )

        # Draw ladders with clean arrow lines.
        for start, end in self.board.ladders.items():
            x1, y1 = self._cell_center(start, size, step, pad)
            x2, y2 = self._cell_center(end, size, step, pad)
            self.board_canvas.create_line(
                x1,
                y1,
                x2,
                y2,
                fill="#2563eb",
                width=max(2, int(step * 0.08)),
                arrow=tk.LAST,
                arrowshape=(10, 12, 5),
            )

        # Draw snakes as curved arrow lines.
        for index, (start, end) in enumerate(self.board.snakes.items()):
            x1, y1 = self._cell_center(start, size, step, pad)
            x2, y2 = self._cell_center(end, size, step, pad)
            direction = -1 if index % 2 == 0 else 1
            control_x = (x1 + x2) / 2 + (direction * max(16.0, step * 0.8))
            control_y = (y1 + y2) / 2 - max(14.0, step * 0.6)
            self.board_canvas.create_line(
                x1,
                y1,
                control_x,
                control_y,
                x2,
                y2,
                smooth=True,
                fill="#dc2626",
                width=max(2, int(step * 0.08)),
                arrow=tk.LAST,
                arrowshape=(10, 12, 5),
            )

        # Mark start and goal cells.
        sx, sy = self._cell_center(1, size, step, pad)
        gx, gy = self._cell_center(self.board.goal, size, step, pad)
        self.board_canvas.create_oval(sx - 8, sy - 8, sx + 8, sy + 8, fill="#2563eb", outline="")
        self.board_canvas.create_text(sx, sy - 16, text="Start", fill="#1e3a8a", font=("Segoe UI", 8, "bold"))
        self.board_canvas.create_oval(gx - 8, gy - 8, gx + 8, gy + 8, fill="#f59e0b", outline="")
        self.board_canvas.create_text(gx, gy - 16, text="Goal", fill="#92400e", font=("Segoe UI", 8, "bold"))

    def _clear_options(self) -> None:
        self.selected_option.set(-1)
        for widget in self.option_buttons:
            widget.destroy()
        self.option_buttons.clear()

    def _render_options(self, options: list[int]) -> None:
        self._clear_options()
        self.selected_option.set(-1)

        for option in options:
            radio = ttk.Radiobutton(
                self.options_container,
                text=str(option),
                value=option,
                variable=self.selected_option,
            )
            radio.pack(anchor=tk.W, pady=2)
            self.option_buttons.append(radio)
