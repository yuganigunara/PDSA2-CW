from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter_ns

from snake_ladder.board import BoardSetup


@dataclass(frozen=True)
class AlgorithmResult:
    minimum_throws: int
    time_ns: int


def timed_bfs(board: BoardSetup, bfs_solver) -> AlgorithmResult:
    start = perf_counter_ns()
    result = bfs_solver(board)
    end = perf_counter_ns()
    return AlgorithmResult(minimum_throws=result, time_ns=end - start)


def timed_dp(board: BoardSetup, dp_solver) -> AlgorithmResult:
    start = perf_counter_ns()
    result = dp_solver(board)
    end = perf_counter_ns()
    return AlgorithmResult(minimum_throws=result, time_ns=end - start)
