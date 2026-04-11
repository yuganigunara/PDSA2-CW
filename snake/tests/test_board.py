import pytest

from snake_ladder.board import (
    MAX_BOARD_SIZE,
    MIN_BOARD_SIZE,
    ValidationError,
    generate_random_board,
    validate_board_size,
)


def test_board_size_validation_accepts_range() -> None:
    validate_board_size(MIN_BOARD_SIZE)
    validate_board_size(MAX_BOARD_SIZE)


def test_board_size_validation_rejects_out_of_range() -> None:
    with pytest.raises(ValidationError):
        validate_board_size(MIN_BOARD_SIZE - 1)

    with pytest.raises(ValidationError):
        validate_board_size(MAX_BOARD_SIZE + 1)


def test_random_board_has_expected_counts() -> None:
    size = 8
    board = generate_random_board(size)

    assert len(board.ladders) == size - 2
    assert len(board.snakes) == size - 2
