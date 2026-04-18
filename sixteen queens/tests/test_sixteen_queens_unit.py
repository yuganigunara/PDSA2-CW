from __future__ import annotations

import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.backtracking import KNOWN_SOLUTIONS, build_sample_board, count_solutions
from app.db import QueensStore
from app.threaded import BenchmarkResult, benchmark_threaded


def test_count_solutions_small_sizes() -> None:
    assert count_solutions(1) == 1
    assert count_solutions(2) == 0
    assert count_solutions(3) == 0
    assert count_solutions(4) == 2
    assert count_solutions(5) == 10


def test_build_sample_board_is_non_attacking() -> None:
    size = 8
    board = build_sample_board(size)

    assert len(board) == size
    assert all(len(row) == size for row in board)

    queen_positions: list[tuple[int, int]] = []
    for row_index, row in enumerate(board):
        assert row.count("Q") == 1
        col_index = row.index("Q")
        queen_positions.append((row_index, col_index))

    cols = {col for _, col in queen_positions}
    pos_diag = {row + col for row, col in queen_positions}
    neg_diag = {row - col for row, col in queen_positions}

    assert len(cols) == size
    assert len(pos_diag) == size
    assert len(neg_diag) == size


def test_threaded_benchmark_small_board() -> None:
    solutions, time_ns, peak_bytes = benchmark_threaded(8)

    assert solutions == 92
    assert time_ns > 0
    assert peak_bytes >= 0


def test_store_round_and_answer_flow(tmp_path: Path) -> None:
    store = QueensStore(path=tmp_path / "sixteen_queens_test.db")

    round_no = store.next_round()
    assert round_no == 1
    assert store.current_round() == 1

    result = BenchmarkResult(
        algorithm="sequential",
        round_no=round_no,
        solutions=KNOWN_SOLUTIONS,
        time_ns=123456,
        peak_bytes=4096,
    )
    store.save_round(result, build_sample_board())

    before = store.dashboard(limit=None)
    assert len(before["rounds"]) == 1
    assert before["rounds"][0]["algorithm"] == "sequential"
    assert before["rounds"][0]["solutions"] == KNOWN_SOLUTIONS
    assert not store.is_recognized(round_no, KNOWN_SOLUTIONS)

    store.save_answer(round_no, "Player One", KNOWN_SOLUTIONS)
    assert store.is_recognized(round_no, KNOWN_SOLUTIONS)

    after = store.dashboard(limit=None)
    assert len(after["answers"]) == 1
    assert after["answers"][0]["player_name"] == "Player One"
    assert after["answers"][0]["answer"] == KNOWN_SOLUTIONS


def test_store_ignores_duplicate_answer_for_same_round(tmp_path: Path) -> None:
    store = QueensStore(path=tmp_path / "sixteen_queens_test.db")
    round_no = store.next_round()

    store.save_answer(round_no, "Player A", KNOWN_SOLUTIONS)
    store.save_answer(round_no, "Player B", KNOWN_SOLUTIONS)

    dashboard = store.dashboard(limit=None)
    answers = dashboard["answers"]

    assert len(answers) == 1
    assert answers[0]["player_name"] == "Player A"
    assert answers[0]["answer"] == KNOWN_SOLUTIONS