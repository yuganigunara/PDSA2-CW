from __future__ import annotations

from dataclasses import dataclass
import random
from typing import Dict


MIN_BOARD_SIZE = 6  # Minimum board size (6x6 grid, 36 cells)
MAX_BOARD_SIZE = 12  # Maximum board size (12x12 grid, 144 cells)
DICE_MIN = 1  # Minimum dice roll value
DICE_MAX = 6  # Maximum dice roll value


class ValidationError(ValueError):
    """Raised when user or board input is invalid."""


class BoardGenerationError(RuntimeError):
    """Raised when a random board cannot be generated safely."""


@dataclass(frozen=True)
class BoardSetup:
    """Immutable game board configuration.
    
    Represents a complete Snakes and Ladders board with size and piece placements.
    
    Attributes:
        size: Board dimensions (size x size grid). Must be between MIN_BOARD_SIZE and MAX_BOARD_SIZE.
        ladders: Mapping of ladder start positions to end positions. Must go upward (start < end).
        snakes: Mapping of snake start positions to end positions. Must go downward (start > end).
    
    Properties:
        goal: The target cell position (size * size, representing the final square).
        jumps: Combined dictionary of all snakes and ladders merged together.
    """
    size: int
    ladders: Dict[int, int]
    snakes: Dict[int, int]

    @property
    def goal(self) -> int:
        return self.size * self.size

    @property
    def jumps(self) -> Dict[int, int]:
        merged = dict(self.ladders)
        merged.update(self.snakes)
        return merged


def validate_board_size(size: int) -> None:
    """Validate board size is within allowed bounds.
    
    Args:
        size: The board dimensions to validate.
    
    Raises:
        ValidationError: If size is not an integer or outside [MIN_BOARD_SIZE, MAX_BOARD_SIZE].
    """
    if not isinstance(size, int):
        raise ValidationError("Board size must be an integer.")
    if size < MIN_BOARD_SIZE or size > MAX_BOARD_SIZE:
        raise ValidationError(
            f"Board size must be between {MIN_BOARD_SIZE} and {MAX_BOARD_SIZE}."
        )


def validate_dice_roll(roll: int) -> None:
    """Validate dice roll is within allowed range.
    
    Args:
        roll: The dice roll value to validate.
    
    Raises:
        ValidationError: If roll is not an integer or outside [DICE_MIN, DICE_MAX].
    """
    if not isinstance(roll, int):
        raise ValidationError("Dice roll must be an integer.")
    if roll < DICE_MIN or roll > DICE_MAX:
        raise ValidationError(f"Dice roll must be between {DICE_MIN} and {DICE_MAX}.")


def validate_board_setup(size: int, ladders: Dict[int, int], snakes: Dict[int, int]) -> None:
    """Validate complete board configuration for consistency and safety.
    
    Ensures:
    - Board size is valid
    - All ladders go upward (start < end)
    - All snakes go downward (start > end)
    - No pieces occupy invalid cells (1 or goal)
    - No overlapping snake/ladder placements
    
    Args:
        size: Board dimensions.
        ladders: Dictionary of ladder positions.
        snakes: Dictionary of snake positions.
    
    Raises:
        ValidationError: If any constraint is violated.
    """
    validate_board_size(size)
    goal = size * size

    occupied_cells = set()

    for start, end in ladders.items():
        if start >= end:
            raise ValidationError(f"Invalid ladder: {start}->{end}. Ladders must go up.")
        if start <= 1 or start >= goal:
            raise ValidationError(f"Invalid ladder start cell: {start}.")
        if end <= 1 or end > goal:
            raise ValidationError(f"Invalid ladder end cell: {end}.")
        if start in occupied_cells or end in occupied_cells:
            raise ValidationError("Snakes and ladders must not overlap.")
        occupied_cells.add(start)
        occupied_cells.add(end)

    for start, end in snakes.items():
        if start <= end:
            raise ValidationError(f"Invalid snake: {start}->{end}. Snakes must go down.")
        if start <= 1 or start > goal:
            raise ValidationError(f"Invalid snake start cell: {start}.")
        if end < 1 or end >= goal:
            raise ValidationError(f"Invalid snake end cell: {end}.")
        if start in occupied_cells or end in occupied_cells:
            raise ValidationError("Snakes and ladders must not overlap.")
        occupied_cells.add(start)
        occupied_cells.add(end)


def generate_random_board(size: int, *, rng: random.Random | None = None) -> BoardSetup:
    validate_board_size(size)
    rng = rng or random.Random()

    ladders_count = size - 2
    snakes_count = size - 2
    goal = size * size

    max_attempts = 500
    for _ in range(max_attempts):
        ladders: Dict[int, int] = {}
        snakes: Dict[int, int] = {}
        used = set()

        try:
            for _ in range(ladders_count):
                candidates = [c for c in range(2, goal) if c not in used and c < goal - 1]
                if not candidates:
                    raise BoardGenerationError("Not enough cells left for ladders.")
                start = rng.choice(candidates)

                end_candidates = [
                    c for c in range(start + 1, goal + 1) if c not in used and c != start
                ]
                if not end_candidates:
                    raise BoardGenerationError("No valid ladder end cell available.")
                end = rng.choice(end_candidates)

                ladders[start] = end
                used.add(start)
                used.add(end)

            for _ in range(snakes_count):
                candidates = [c for c in range(2, goal + 1) if c not in used and c > 2]
                if not candidates:
                    raise BoardGenerationError("Not enough cells left for snakes.")
                start = rng.choice(candidates)

                end_candidates = [
                    c for c in range(1, start) if c not in used and c != start and c < goal
                ]
                if not end_candidates:
                    raise BoardGenerationError("No valid snake end cell available.")
                end = rng.choice(end_candidates)

                snakes[start] = end
                used.add(start)
                used.add(end)

            validate_board_setup(size, ladders, snakes)
            return BoardSetup(size=size, ladders=ladders, snakes=snakes)
        except (ValidationError, BoardGenerationError):
            continue

    raise BoardGenerationError(
        "Failed to generate a valid random board with non-overlapping snakes and ladders."
    )
