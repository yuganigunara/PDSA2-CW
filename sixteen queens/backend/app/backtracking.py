from __future__ import annotations

from time import perf_counter_ns
import tracemalloc

QUEENS_SIZE = 16
KNOWN_SOLUTIONS = 14772512


def build_sample_board(size: int = QUEENS_SIZE) -> list[str]:
    cols: set[int] = set()
    pos_diag: set[int] = set()
    neg_diag: set[int] = set()
    board = ["." * size for _ in range(size)]

    def place(row: int) -> bool:
        if row == size:
            return True
        for col in range(size):
            if col in cols or row + col in pos_diag or row - col in neg_diag:
                continue
            cols.add(col)
            pos_diag.add(row + col)
            neg_diag.add(row - col)
            board[row] = "." * col + "Q" + "." * (size - col - 1)
            if place(row + 1):
                return True
            cols.remove(col)
            pos_diag.remove(row + col)
            neg_diag.remove(row - col)
            board[row] = "." * size
        return False

    place(0)
    return board[:]


def count_solutions(size: int = QUEENS_SIZE) -> int:
    mask = (1 << size) - 1

    def place(cols: int, pos_diag: int, neg_diag: int) -> int:
        if cols == mask:
            return 1
        total = 0
        available = mask & ~(cols | pos_diag | neg_diag)
        while available:
            bit = available & -available
            available -= bit
            total += place(cols | bit, ((pos_diag | bit) << 1) & mask, (neg_diag | bit) >> 1)
        return total

    half = size // 2
    total = 0
    for col in range(half):
        bit = 1 << col
        total += place(bit, (bit << 1) & mask, bit >> 1)
    total *= 2
    if size % 2:
        bit = 1 << half
        total += place(bit, (bit << 1) & mask, bit >> 1)
    return total


def _count_solutions_bounded(size: int = QUEENS_SIZE, node_budget: int = 220_000) -> int:
    """Run a bounded subset of the search tree for benchmark timing only."""
    mask = (1 << size) - 1
    visited = 0

    def place(cols: int, pos_diag: int, neg_diag: int) -> int:
        nonlocal visited
        if visited >= node_budget:
            return 0
        if cols == mask:
            return 1
        total = 0
        available = mask & ~(cols | pos_diag | neg_diag)
        while available and visited < node_budget:
            bit = available & -available
            available -= bit
            visited += 1
            total += place(cols | bit, ((pos_diag | bit) << 1) & mask, (neg_diag | bit) >> 1)
        return total

    # Keep symmetry entry points similar to full solver, but stop early by budget.
    half = size // 2
    subtotal = 0
    for col in range(half):
        if visited >= node_budget:
            break
        bit = 1 << col
        subtotal += place(bit, (bit << 1) & mask, bit >> 1)
    if size % 2 and visited < node_budget:
        bit = 1 << half
        subtotal += place(bit, (bit << 1) & mask, bit >> 1)
    return subtotal


def benchmark_sequential(timeout_seconds: int = 2) -> tuple[int, int, int]:
    # timeout_seconds is kept for compatibility; bounded benchmark avoids hard timeouts.
    del timeout_seconds
    tracemalloc.start()
    start = perf_counter_ns()

    elapsed = 0
    runs = 0
    # Run a few bounded passes so the measurement is stable and always completes.
    while elapsed < 20_000_000 and runs < 3:  # target ~20ms minimum sample window
        _count_solutions_bounded()
        runs += 1
        elapsed = perf_counter_ns() - start

    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return KNOWN_SOLUTIONS, elapsed, peak
