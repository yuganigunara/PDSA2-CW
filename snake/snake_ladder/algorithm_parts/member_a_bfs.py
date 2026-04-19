from __future__ import annotations

from collections import deque

from snake_ladder.board import BoardSetup, ValidationError, validate_board_setup


def _next_cell(cell: int, roll: int, goal: int, jumps: dict[int, int]) -> int | None:
    destination = cell + roll
    if destination > goal:
        return None
    return jumps.get(destination, destination)


def min_throws_bfs(board: BoardSetup) -> int:
    validate_board_setup(board.size, board.ladders, board.snakes)
    goal = board.goal
    jumps = board.jumps

    visited = {1}
    queue = deque([(1, 0)])

    while queue:
        cell, throws = queue.popleft()
        if cell == goal:
            return throws

        for roll in range(1, 7):
            nxt = _next_cell(cell, roll, goal, jumps)
            if nxt is None:
                continue
            if nxt not in visited:
                visited.add(nxt)
                queue.append((nxt, throws + 1))

    raise ValidationError("Goal is unreachable for this board setup.")
