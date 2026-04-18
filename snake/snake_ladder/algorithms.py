<<<<<<< Updated upstream
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from math import inf
from time import perf_counter_ns
from typing import Dict

from snake_ladder.board import BoardSetup, ValidationError, validate_board_setup


@dataclass(frozen=True)
class AlgorithmResult:
    minimum_throws: int
    time_ns: int


def _next_cell(cell: int, roll: int, goal: int, jumps: Dict[int, int]) -> int | None:
    destination = cell + roll
    if destination > goal:
        return None
    return jumps.get(destination, destination)


def min_throws_bfs(board: BoardSetup) -> int:
    validate_board_setup(board.size, board.ladders, board.snakes)
    goal = board.goal
    jumps = board.jumps

    visited = set([1])
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


def min_throws_dp(board: BoardSetup) -> int:
    validate_board_setup(board.size, board.ladders, board.snakes)
    goal = board.goal
    jumps = board.jumps

    dp = [inf] * (goal + 1)
    dp[1] = 0
=======
from math import inf
from time import perf_counter_ns

def _next_cell(cell: int, roll: int, goal: int, jumps: dict[int, int]) -> int | None:
    raw_next = cell + roll
    if raw_next > goal:
        return None
    return jumps.get(raw_next, raw_next)


def min_throws_dp(goal: int, jumps: dict[int, int], start: int = 1) -> int:
    if goal < 1:
        raise ValueError("Goal must be a positive integer.")
    if start < 1 or start > goal:
        raise ValueError("Start must be between 1 and goal.")

    dp = [inf] * (goal + 1)
    dp[start] = 0
>>>>>>> Stashed changes

    # Bellman-Ford style relaxation with unit edge cost handles snake back-edges safely.
    for _ in range(goal - 1):
        changed = False
<<<<<<< Updated upstream
        for cell in range(1, goal + 1):
=======
        for cell in range(start, goal + 1):
>>>>>>> Stashed changes
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
<<<<<<< Updated upstream
        raise ValidationError("Goal is unreachable for this board setup.")
=======
        raise ValueError("Goal is unreachable for this board setup.")
>>>>>>> Stashed changes

    return int(dp[goal])


<<<<<<< Updated upstream
def timed_bfs(board: BoardSetup) -> AlgorithmResult:
    start = perf_counter_ns()
    result = min_throws_bfs(board)
    end = perf_counter_ns()
    return AlgorithmResult(minimum_throws=result, time_ns=end - start)


def timed_dp(board: BoardSetup) -> AlgorithmResult:
    start = perf_counter_ns()
    result = min_throws_dp(board)
    end = perf_counter_ns()
    return AlgorithmResult(minimum_throws=result, time_ns=end - start)
=======
def timed_dp(goal: int, jumps: dict[int, int], start: int = 1) -> dict[str, int]:
    timer_start = perf_counter_ns()
    result = min_throws_dp(goal, jumps, start)
    timer_end = perf_counter_ns()
    return {"minimum_throws": result, "time_ns": timer_end - timer_start}
>>>>>>> Stashed changes
