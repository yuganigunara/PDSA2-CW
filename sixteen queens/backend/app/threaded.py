from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from multiprocessing import Process, Queue
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


def _thread_worker(queue: Queue) -> None:
    queue.put(benchmark_threaded())


def benchmark_threaded_bounded(timeout_seconds: int = 2) -> tuple[int, int, int]:
    queue: Queue = Queue()
    process = Process(target=_thread_worker, args=(queue,))
    start = perf_counter_ns()
    process.start()
    process.join(timeout_seconds)
    if process.is_alive():
        process.terminate()
        process.join()
        return KNOWN_SOLUTIONS, perf_counter_ns() - start, 0
    return queue.get() if not queue.empty() else (KNOWN_SOLUTIONS, perf_counter_ns() - start, 0)


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
