from __future__ import annotations

from dataclasses import dataclass

OFFSETS: tuple[tuple[int, int], ...] = (
    (2, 1),
    (2, -1),
    (-2, 1),
    (-2, -1),
    (1, 2),
    (1, -2),
    (-1, 2),
    (-1, -2),
)


@dataclass(frozen=True)
class Position:
    row: int
    col: int

    def key(self) -> str:
        return f"{self.row},{self.col}"

    def label(self) -> str:
        return f"({self.row + 1}, {self.col + 1})"


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    reason: str
    coverage: float


def is_inside_board(size: int, row: int, col: int) -> bool:
    return 0 <= row < size and 0 <= col < size


def is_knight_move(start: Position, end: Position) -> bool:
    d_row = abs(start.row - end.row)
    d_col = abs(start.col - end.col)
    return (d_row == 2 and d_col == 1) or (d_row == 1 and d_col == 2)


def get_possible_moves(
    size: int,
    row: int,
    col: int,
    visited: set[str] | None = None,
) -> list[Position]:
    visited = visited or set()
    moves: list[Position] = []
    for d_row, d_col in OFFSETS:
        next_row = row + d_row
        next_col = col + d_col
        candidate = Position(next_row, next_col)
        if is_inside_board(size, next_row, next_col) and candidate.key() not in visited:
            moves.append(candidate)
    return moves


def _onward_count(size: int, move: Position, visited: set[str]) -> int:
    with_candidate = set(visited)
    with_candidate.add(move.key())
    return len(get_possible_moves(size, move.row, move.col, with_candidate))


def solve_warnsdorff(size: int, start: Position) -> list[Position] | None:
    visited = {start.key()}
    path = [start]

    while len(path) < size * size:
        current = path[-1]
        candidates = get_possible_moves(size, current.row, current.col, visited)
        if not candidates:
            return None

        candidates.sort(key=lambda move: _onward_count(size, move, visited))
        chosen = candidates[0]
        path.append(chosen)
        visited.add(chosen.key())

    return path


def solve_backtracking(
    size: int,
    start: Position,
    node_limit: int = 3_500_000,
) -> list[Position] | None:
    visited_grid = [[False] * size for _ in range(size)]
    visited_keys: set[str] = set()
    path: list[Position] = [Position(-1, -1)] * (size * size)
    visited_nodes = 0

    def dfs(row: int, col: int, move_index: int) -> bool:
        nonlocal visited_nodes
        visited_nodes += 1
        if visited_nodes > node_limit:
            return False

        position = Position(row, col)
        visited_grid[row][col] = True
        visited_keys.add(position.key())
        path[move_index] = position

        if move_index == size * size - 1:
            return True

        moves = get_possible_moves(size, row, col, visited_keys)
        moves.sort(key=lambda move: _onward_count(size, move, visited_keys))

        for next_move in moves:
            if not visited_grid[next_move.row][next_move.col] and dfs(next_move.row, next_move.col, move_index + 1):
                return True

        visited_grid[row][col] = False
        visited_keys.remove(position.key())
        return False

    solved = dfs(start.row, start.col, 0)
    return path if solved else None


def validate_path(size: int, path: list[Position], start: Position) -> ValidationResult:
    if not path:
        return ValidationResult(False, "Path is empty", 0.0)

    target = size * size
    if path[0] != start:
        return ValidationResult(False, "Path does not start at the required square", len(path) / target)

    visited: set[str] = set()
    for index, current in enumerate(path):
        if not is_inside_board(size, current.row, current.col):
            return ValidationResult(False, f"Move {index + 1} is outside the board", index / target)

        key = current.key()
        if key in visited:
            return ValidationResult(False, f"Square repeated at move {index + 1}", index / target)
        visited.add(key)

        if index > 0 and not is_knight_move(path[index - 1], current):
            return ValidationResult(False, f"Move {index + 1} is not a legal knight move", index / target)

    if len(path) != target:
        return ValidationResult(False, "Path is incomplete", len(path) / target)

    return ValidationResult(True, "Valid complete tour", 1.0)
