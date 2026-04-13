from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List

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
    QueensValidationError,
    benchmark_sixteen_queens,
    compare_speed_text,
    validate_numeric_answer,
    validate_player_name,
)


@dataclass(frozen=True)
class RoundResult:
    board_size: int
    correct_answer: int
    selected_answer: int
    bfs_time_ns: int
    dp_time_ns: int
    outcome: str


class SnakeAndLadderGame:
    def __init__(self, repository: ResultRepository | None = None) -> None:
        self.repository = repository or ResultRepository()

    def run(self) -> None:
        try:
            while True:
                print("\n=== Snake and Ladder Menu ===")
                print("1. Play Snake and Ladder Round")
                print("2. Play Sixteen Queens Puzzle")
                print("3. Exit")

                choice = input("Select option: ").strip()
                if choice == "1":
                    self.play_round()
                elif choice == "2":
                    self.play_sixteen_queens_puzzle()
                elif choice == "3":
                    print("Goodbye!")
                    return
                else:
                    print("Invalid menu option. Enter 1, 2, or 3.")
        except KeyboardInterrupt:
            print("\nGame interrupted. Goodbye!")
            return

    def play_sixteen_queens_puzzle(self) -> None:
        print("\n=== Sixteen Queens Puzzle ===")
        print(
            "Place 16 queens on a 16x16 board so that no two queens threaten each other."
        )

        try:
            use_cached = input("Use latest benchmark if available? (y/n): ").strip().lower()
            benchmark = self.repository.get_latest_queens_benchmark() if use_cached == "y" else None

            if benchmark is None:
                print("Running sequential and threaded programs... this may take some time.")
                benchmark = benchmark_sixteen_queens()
                self.repository.save_queens_benchmark(benchmark)
                print("Benchmark saved.")

            print(f"\nSequential solutions: {benchmark.sequential_solutions}")
            print(f"Sequential time: {benchmark.sequential_time_ns} ns")
            print(f"Threaded solutions: {benchmark.threaded_solutions}")
            print(f"Threaded time: {benchmark.threaded_time_ns} ns")
            print(compare_speed_text(benchmark))

            if benchmark.sequential_solutions != benchmark.threaded_solutions:
                print("Algorithms disagree. Puzzle round is DRAW.")
                return

            player_name = validate_player_name(input("Enter player name: "))
            answer = validate_numeric_answer(
                input("Enter maximum number of solutions for 16 queens: ")
            )

            correct = benchmark.sequential_solutions
            if answer != correct:
                print(f"Incorrect. Correct answer is {correct}.")
                return

            cycle_id = self.repository.get_current_queens_cycle()
            if self.repository.has_recognized_queens_answer(answer=answer, cycle_id=cycle_id):
                print(
                    "This correct response is already recognized in the current cycle. "
                    "Try again with a new cycle."
                )
                return

            self.repository.save_queens_correct_answer(
                player_name=player_name,
                answer=answer,
                cycle_id=cycle_id,
            )
            print("Correct answer saved with player name.")

            # This puzzle has one numeric target response; once identified, reset cycle for future players.
            self.repository.reset_queens_recognition_cycle()
            print("Recognition cycle reset. Future players can submit the same correct response.")

        except QueensValidationError as exc:
            print(f"Validation error: {exc}")
        except DatabaseError as exc:
            print(f"Database error: {exc}")

    def play_round(self) -> RoundResult | None:
        try:
            size = self._read_board_size()
            player_name = self._read_player_name()

            board = generate_random_board(size)
            bfs = timed_bfs(board)
            dp = timed_dp(board)

            if bfs.minimum_throws != dp.minimum_throws:
                print("\nBFS and DP gave different answers. Round result is DRAW.")
                print(f"BFS: {bfs.minimum_throws} throws")
                print(f"DP : {dp.minimum_throws} throws")
                return RoundResult(
                    board_size=size,
                    correct_answer=bfs.minimum_throws,
                    selected_answer=-1,
                    bfs_time_ns=bfs.time_ns,
                    dp_time_ns=dp.time_ns,
                    outcome="DRAW",
                )

            correct = bfs.minimum_throws
            options = self._build_answer_options(correct)

            print("\nBoard Generated")
            print(f"Size: {size}x{size}")
            print(f"Ladders: {board.ladders}")
            print(f"Snakes : {board.snakes}")
            print("\nWhat is the minimum number of dice throws to reach the final cell?")
            for idx, option in enumerate(options, start=1):
                print(f"{idx}. {option}")

            selected_index = self._read_answer_choice()
            selected_answer = options[selected_index - 1]

            if selected_answer == correct:
                print("\nWIN: Correct answer!")
                print(f"Minimum throws: {correct}")
                print(f"BFS time: {bfs.time_ns} ns")
                print(f"DP time : {dp.time_ns} ns")
                try:
                    self.repository.save_correct_answer(
                        player_name=player_name,
                        answer=correct,
                        bfs_time_ns=bfs.time_ns,
                        dp_time_ns=dp.time_ns,
                        board=board,
                    )
                    print("Result saved to database.")
                except DatabaseError as exc:
                    print(f"Database error while saving result: {exc}")
                return RoundResult(
                    board_size=size,
                    correct_answer=correct,
                    selected_answer=selected_answer,
                    bfs_time_ns=bfs.time_ns,
                    dp_time_ns=dp.time_ns,
                    outcome="WIN",
                )

            print("\nLOSE: Incorrect answer.")
            print(f"Your answer: {selected_answer}")
            print(f"Correct answer: {correct}")
            print(f"BFS time: {bfs.time_ns} ns")
            print(f"DP time : {dp.time_ns} ns")
            return RoundResult(
                board_size=size,
                correct_answer=correct,
                selected_answer=selected_answer,
                bfs_time_ns=bfs.time_ns,
                dp_time_ns=dp.time_ns,
                outcome="LOSE",
            )

        except ValidationError as exc:
            print(f"Validation error: {exc}")
            return None

    def _read_board_size(self) -> int:
        raw = input(
            f"Enter board size N ({MIN_BOARD_SIZE}-{MAX_BOARD_SIZE}): "
        ).strip()

        if not raw.isdigit():
            raise ValidationError("Board size must be numeric.")

        size = int(raw)
        validate_board_size(size)
        return size

    def _read_player_name(self) -> str:
        name = input("Enter your name: ").strip()
        if not name:
            raise ValidationError("Player name cannot be empty.")
        if len(name) > 50:
            raise ValidationError("Player name is too long.")
        return name

    def _read_answer_choice(self) -> int:
        raw = input("Choose option (1-3): ").strip()
        if raw not in {"1", "2", "3"}:
            raise ValidationError("Answer option must be 1, 2, or 3.")
        return int(raw)

    def _build_answer_options(self, correct: int) -> List[int]:
        low = max(1, correct - 3)
        high = correct + 3

        options = {correct}
        while len(options) < 3:
            options.add(random.randint(low, high))

        shuffled = list(options)
        random.shuffle(shuffled)
        return shuffled
