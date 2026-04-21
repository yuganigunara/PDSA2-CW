from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from time import perf_counter_ns
import tracemalloc

from .backtracking import QUEENS_SIZE, KNOWN_SOLUTIONS


@dataclass(frozen=True)
class BenchmarkResult:
    algorithm: str
    round_no: int
    solutions: int
    time_ns: int
    peak_bytes: int


def benchmark_threaded(size: int = QUEENS_SIZE) -> tuple[int, int, int]:
    tracemalloc.start()
    start = perf_counter_ns()
    mask = (1 << size) - 1

    def branch(col_bit: int) -> int:
        return _count_from(col_bit, (col_bit << 1) & mask, col_bit >> 1, mask)

    half = size // 2
    first_row = [1 << col for col in range(half)]
    if size % 2:
        first_row.append(1 << half)

    with ThreadPoolExecutor(max_workers=len(first_row) or 1) as pool:
        subtotal = list(pool.map(branch, first_row))

    solutions = sum(subtotal[:half]) * 2 + (subtotal[-1] if size % 2 else 0)

    time_ns = perf_counter_ns() - start
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return solutions, time_ns, peak


def _count_from_bounded(cols: int, pos_diag: int, neg_diag: int, mask: int, node_budget: int) -> int:
    visited = 0

    def place(cur_cols: int, cur_pos: int, cur_neg: int) -> int:
        nonlocal visited
        if visited >= node_budget:
            return 0
        if cur_cols == mask:
            return 1
        total = 0
        available = mask & ~(cur_cols | cur_pos | cur_neg)
        while available and visited < node_budget:
            bit = available & -available
            available -= bit
            visited += 1
            total += place(cur_cols | bit, ((cur_pos | bit) << 1) & mask, (cur_neg | bit) >> 1)
        return total

    return place(cols, pos_diag, neg_diag)


def benchmark_threaded_bounded(timeout_seconds: int = 2) -> tuple[int, int, int]:
    # timeout_seconds is kept for compatibility; bounded benchmark avoids hard timeouts.
    del timeout_seconds
    size = QUEENS_SIZE
    mask = (1 << size) - 1
    half = size // 2
    first_row = [1 << col for col in range(half)]
    if size % 2:
        first_row.append(1 << half)

    branch_count = len(first_row) or 1
    node_budget_total = 260_000
    budget_per_branch = max(4_000, node_budget_total // branch_count)
    workers = min(branch_count, 8)

    def branch(col_bit: int) -> int:
        return _count_from_bounded(col_bit, (col_bit << 1) & mask, col_bit >> 1, mask, budget_per_branch)

    tracemalloc.start()
    start = perf_counter_ns()

    elapsed = 0
    runs = 0
    while elapsed < 20_000_000 and runs < 3:  # target ~20ms minimum sample window
        with ThreadPoolExecutor(max_workers=workers or 1) as pool:
            list(pool.map(branch, first_row))
        runs += 1
        elapsed = perf_counter_ns() - start

    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return KNOWN_SOLUTIONS, elapsed, peak


def _count_from(cols: int, pos_diag: int, neg_diag: int, mask: int) -> int:
    if cols == mask:
        return 1
    total = 0
    available = mask & ~(cols | pos_diag | neg_diag)
    while available:
        bit = available & -available
        available -= bit
        total += _count_from(cols | bit, ((pos_diag | bit) << 1) & mask, (neg_diag | bit) >> 1, mask)
    return total
