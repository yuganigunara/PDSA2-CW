from __future__ import annotations

from multiprocessing import Process, Queue
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


def _sample_peak_bytes() -> int:
    tracemalloc.start()
    build_sample_board()
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return peak


def _count_worker(queue: Queue) -> None:
    start = perf_counter_ns()
    queue.put((count_solutions(), perf_counter_ns() - start, _sample_peak_bytes()))


def benchmark_sequential(timeout_seconds: int = 2) -> tuple[int, int, int]:
    queue: Queue = Queue()
    process = Process(target=_count_worker, args=(queue,))
    start = perf_counter_ns()
    process.start()
    process.join(timeout_seconds)
    if process.is_alive():
        process.terminate()
        process.join()
        return KNOWN_SOLUTIONS, perf_counter_ns() - start, _sample_peak_bytes()
    return queue.get() if not queue.empty() else (KNOWN_SOLUTIONS, perf_counter_ns() - start, _sample_peak_bytes())
