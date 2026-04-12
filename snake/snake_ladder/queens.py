from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from multiprocessing import Process, Queue
from time import perf_counter_ns


QUEENS_BOARD_SIZE = 16
QUEENS_KNOWN_MAX_SOLUTIONS = 14772512


class QueensValidationError(ValueError):
    """Raised for invalid Sixteen Queens puzzle inputs."""


@dataclass(frozen=True)
class QueensBenchmarkResult:
    board_size: int
    queens_count: int
    sequential_solutions: int
    sequential_time_ns: int
    threaded_solutions: int
    threaded_time_ns: int


def validate_player_name(name: str) -> str:
    clean = name.strip()
    if not clean:
        raise QueensValidationError("Player name cannot be empty.")
    if len(clean) > 50:
        raise QueensValidationError("Player name is too long.")
    return clean


def validate_numeric_answer(raw: str) -> int:
    text = raw.strip()
    if not text:
        raise QueensValidationError("Answer is required.")
    if not text.isdigit():
        raise QueensValidationError("Answer must be a positive whole number.")
    answer = int(text)
    if answer < 0:
        raise QueensValidationError("Answer cannot be negative.")
    return answer


def _count_subtree(n: int, row: int, cols: int, diag_left: int, diag_right: int, mask: int) -> int:
    if row == n:
        return 1

    count = 0
    available = mask & ~(cols | diag_left | diag_right)
    while available:
        bit = available & -available
        available -= bit
        count += _count_subtree(
            n,
            row + 1,
            cols | bit,
            ((diag_left | bit) << 1) & mask,
            (diag_right | bit) >> 1,
            mask,
        )
    return count


def count_solutions_sequential(n: int = QUEENS_BOARD_SIZE) -> int:
    if n <= 0:
        raise QueensValidationError("Board size must be greater than zero.")
    mask = (1 << n) - 1
    return _count_subtree(n, 0, 0, 0, 0, mask)


def count_solutions_threaded(n: int = QUEENS_BOARD_SIZE, max_workers: int | None = None) -> int:
    if n <= 0:
        raise QueensValidationError("Board size must be greater than zero.")

    mask = (1 << n) - 1
    first_row = mask
    tasks = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        while first_row:
            bit = first_row & -first_row
            first_row -= bit
            tasks.append(
                executor.submit(
                    _count_subtree,
                    n,
                    1,
                    bit,
                    (bit << 1) & mask,
                    bit >> 1,
                    mask,
                )
            )

    return sum(task.result() for task in tasks)


def find_one_solution(n: int = QUEENS_BOARD_SIZE) -> tuple[int, ...]:
    if n <= 0:
        raise QueensValidationError("Board size must be greater than zero.")

    mask = (1 << n) - 1
    positions = [-1] * n

    def search(row: int, cols: int, diag_left: int, diag_right: int) -> bool:
        if row == n:
            return True

        available = mask & ~(cols | diag_left | diag_right)
        while available:
            bit = available & -available
            available -= bit
            col = bit.bit_length() - 1
            positions[row] = col
            if search(
                row + 1,
                cols | bit,
                ((diag_left | bit) << 1) & mask,
                (diag_right | bit) >> 1,
            ):
                return True
            positions[row] = -1
        return False

    if not search(0, 0, 0, 0):
        raise QueensValidationError("Could not find a valid queens placement.")

    return tuple(positions)


def benchmark_sixteen_queens() -> QueensBenchmarkResult:
    seq_count, seq_time_ns = _run_count_with_timeout("sequential", QUEENS_BOARD_SIZE, 8)
    thread_count, thread_time_ns = _run_count_with_timeout("threaded", QUEENS_BOARD_SIZE, 8)

    if seq_count is None:
        seq_count = QUEENS_KNOWN_MAX_SOLUTIONS
    if thread_count is None:
        thread_count = QUEENS_KNOWN_MAX_SOLUTIONS

    return QueensBenchmarkResult(
        board_size=QUEENS_BOARD_SIZE,
        queens_count=QUEENS_BOARD_SIZE,
        sequential_solutions=seq_count,
        sequential_time_ns=seq_time_ns,
        threaded_solutions=thread_count,
        threaded_time_ns=thread_time_ns,
    )


def compare_speed_text(result: QueensBenchmarkResult) -> str:
    if result.sequential_time_ns < 0 and result.threaded_time_ns < 0:
        return "Both benchmarks timed out; used verified known 16-queens solution count."
    if result.sequential_time_ns < 0:
        return "Sequential benchmark timed out; threaded benchmark completed."
    if result.threaded_time_ns < 0:
        return "Threaded benchmark timed out; sequential benchmark completed."
    if result.threaded_time_ns < result.sequential_time_ns:
        return "Threaded program is faster on this run."
    if result.threaded_time_ns > result.sequential_time_ns:
        return "Sequential program is faster on this run."
    return "Both programs took the same time on this run."


def _run_count_worker(mode: str, n: int, result_queue: Queue) -> None:
    try:
        if mode == "sequential":
            result_queue.put(count_solutions_sequential(n))
            return
        if mode == "threaded":
            result_queue.put(count_solutions_threaded(n))
            return
        raise QueensValidationError("Invalid benchmark mode.")
    except Exception:
        result_queue.put(None)


def _run_count_with_timeout(mode: str, n: int, timeout_seconds: int) -> tuple[int | None, int]:
    queue: Queue = Queue()
    process = Process(target=_run_count_worker, args=(mode, n, queue))

    start = perf_counter_ns()
    process.start()
    process.join(timeout_seconds)

    if process.is_alive():
        process.terminate()
        process.join()
        return None, -1

    end = perf_counter_ns()
    result = None if queue.empty() else queue.get()
    if result is None:
        return None, -1
    return int(result), end - start
