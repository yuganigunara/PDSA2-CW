from __future__ import annotations

from math import inf

from snake_ladder.board import BoardSetup, ValidationError, validate_board_setup


def _next_cell(cell: int, roll: int, goal: int, jumps: dict[int, int]) -> int | None:
    destination = cell + roll
    if destination > goal:
        return None
    return jumps.get(destination, destination)


def min_throws_dp(board: BoardSetup) -> int:
    validate_board_setup(board.size, board.ladders, board.snakes)
    goal = board.goal
    jumps = board.jumps

    dp = [inf] * (goal + 1)
    dp[1] = 0

    # Bellman-Ford style relaxation with unit edge cost handles snake back-edges safely.
    for _ in range(goal - 1):
        changed = False
        for cell in range(1, goal + 1):
            if dp[cell] == inf:
                continue
            for roll in range(1, 7):
                nxt = _next_cell(cell, roll, goal, jumps)
                if nxt is None:
                    continue
                candidate = dp[cell] + 1
                if candidate < dp[nxt]:
                    dp[nxt] = candidate
                    changed = True
        if not changed:
            break

    if dp[goal] == inf:
        raise ValidationError("Goal is unreachable for this board setup.")

    return int(dp[goal])
