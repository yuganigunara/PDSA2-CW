from pathlib import Path

import pytest

from snake_ladder.database import DatabaseError, ResultRepository
from snake_ladder.queens import (
    QueensBenchmarkResult,
    QueensValidationError,
    count_solutions_sequential,
    count_solutions_threaded,
    validate_numeric_answer,
    validate_player_name,
)


def test_queens_sequential_and_threaded_match_for_n8() -> None:
    seq = count_solutions_sequential(8)
    threaded = count_solutions_threaded(8)

    assert seq == 92
    assert threaded == 92


def test_queens_invalid_board_size_raises() -> None:
    with pytest.raises(QueensValidationError):
        count_solutions_sequential(0)

    with pytest.raises(QueensValidationError):
        count_solutions_threaded(-1)


def test_queens_validations() -> None:
    assert validate_player_name(" Alice ") == "Alice"
    assert validate_numeric_answer(" 123 ") == 123

    with pytest.raises(QueensValidationError):
        validate_player_name("   ")

    with pytest.raises(QueensValidationError):
        validate_numeric_answer("abc")


def test_queens_database_benchmark_and_duplicate_handling(tmp_path: Path) -> None:
    db_path = tmp_path / "queens_test.db"
    repo = ResultRepository(str(db_path))

    benchmark = QueensBenchmarkResult(
        board_size=16,
        queens_count=16,
        sequential_solutions=14772512,
        sequential_time_ns=100,
        threaded_solutions=14772512,
        threaded_time_ns=90,
    )

    repo.save_queens_benchmark(benchmark)
    latest = repo.get_latest_queens_benchmark()

    assert latest is not None
    assert latest.sequential_solutions == 14772512

    cycle = repo.get_current_queens_cycle()
    repo.save_queens_correct_answer(player_name="Alice", answer=14772512, cycle_id=cycle)

    assert repo.has_recognized_queens_answer(answer=14772512, cycle_id=cycle)

    with pytest.raises(DatabaseError):
        repo.save_queens_correct_answer(player_name="Bob", answer=14772512, cycle_id=cycle)

    repo.reset_queens_recognition_cycle()
    next_cycle = repo.get_current_queens_cycle()
    assert next_cycle == cycle + 1
    assert not repo.has_recognized_queens_answer(answer=14772512, cycle_id=next_cycle)
