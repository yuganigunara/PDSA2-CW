import pytest

from snake_ladder.board import (
    ValidationError,
    validate_board_setup,
    validate_dice_roll,
)


def test_validate_dice_roll_rejects_invalid_values() -> None:
    with pytest.raises(ValidationError):
        validate_dice_roll(0)

    with pytest.raises(ValidationError):
        validate_dice_roll(7)


def test_validate_board_setup_rejects_overlap() -> None:
    with pytest.raises(ValidationError):
        validate_board_setup(
            6,
            ladders={2: 12},
            snakes={12: 4},
        )


def test_validate_board_setup_rejects_invalid_direction() -> None:
    with pytest.raises(ValidationError):
        validate_board_setup(
            6,
            ladders={14: 3},
            snakes={},
        )
