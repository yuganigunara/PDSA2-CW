from __future__ import annotations

import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.backtracking import BOARD_SIZE, DEFAULT_QUEEN_COUNT, build_sample_board, count_solutions, known_solutions_for_queen_count
from app.db import QueensStore
from app.threaded import BenchmarkResult, benchmark_threaded


def test_count_solutions_supported_queen_counts() -> None:
    assert count_solutions(8) == known_solutions_for_queen_count(8)
    assert count_solutions(16) == 14772512


def test_build_sample_board_is_non_attacking() -> None:
    queen_count = 8
    board = build_sample_board(queen_count)

    assert len(board) == BOARD_SIZE
    assert all(len(row) == BOARD_SIZE for row in board)

    queen_positions: list[tuple[int, int]] = []
    for row_index, row in enumerate(board):
        if "Q" not in row:
            continue
        assert row.count("Q") == 1
        col_index = row.index("Q")
        queen_positions.append((row_index, col_index))

    cols = {col for _, col in queen_positions}
    pos_diag = {row + col for row, col in queen_positions}
    neg_diag = {row - col for row, col in queen_positions}

    assert len(queen_positions) == queen_count
    assert len(cols) == queen_count
    assert len(pos_diag) == queen_count
    assert len(neg_diag) == queen_count


def test_threaded_benchmark_small_board() -> None:
    solutions, time_ns, peak_bytes = benchmark_threaded(8)

    assert solutions == known_solutions_for_queen_count(8)
    assert time_ns > 0
    assert peak_bytes >= 0


def test_store_round_and_answer_flow(tmp_path: Path) -> None:
    store = QueensStore(path=tmp_path / "sixteen_queens_test.db")

    round_no = store.next_round(DEFAULT_QUEEN_COUNT)
    assert round_no == 1
    assert store.current_round(DEFAULT_QUEEN_COUNT) == 1

    result = BenchmarkResult(
        algorithm="sequential",
        round_no=round_no,
        solutions=known_solutions_for_queen_count(DEFAULT_QUEEN_COUNT),
        time_ns=123456,
        peak_bytes=4096,
    )
    store.save_round(DEFAULT_QUEEN_COUNT, result, build_sample_board(DEFAULT_QUEEN_COUNT))

    before = store.dashboard(DEFAULT_QUEEN_COUNT, limit=None)
    assert len(before["rounds"]) == 1
    assert before["rounds"][0]["algorithm"] == "sequential"
    assert before["rounds"][0]["solutions"] == known_solutions_for_queen_count(DEFAULT_QUEEN_COUNT)
    assert not store.is_recognized(round_no, DEFAULT_QUEEN_COUNT, known_solutions_for_queen_count(DEFAULT_QUEEN_COUNT))

    store.save_answer(round_no, DEFAULT_QUEEN_COUNT, "Player One", known_solutions_for_queen_count(DEFAULT_QUEEN_COUNT))
    assert store.is_recognized(round_no, DEFAULT_QUEEN_COUNT, known_solutions_for_queen_count(DEFAULT_QUEEN_COUNT))

    after = store.dashboard(DEFAULT_QUEEN_COUNT, limit=None)
    assert len(after["answers"]) == 1
    assert after["answers"][0]["player_name"] == "Player One"
    assert after["answers"][0]["answer"] == known_solutions_for_queen_count(DEFAULT_QUEEN_COUNT)


def test_store_ignores_duplicate_answer_for_same_round(tmp_path: Path) -> None:
    store = QueensStore(path=tmp_path / "sixteen_queens_test.db")
    round_no = store.next_round(8)

    store.save_answer(round_no, 8, "Player A", known_solutions_for_queen_count(8))
    store.save_answer(round_no, 8, "Player B", known_solutions_for_queen_count(8))

    dashboard = store.dashboard(8, limit=None)
    answers = dashboard["answers"]

    assert len(answers) == 1
    assert answers[0]["player_name"] == "Player A"
    assert answers[0]["answer"] == known_solutions_for_queen_count(8)