from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .backtracking import (
    BOARD_SIZE,
    DEFAULT_QUEEN_COUNT,
    SUPPORTED_QUEEN_COUNTS,
    benchmark_sequential_for_queen_count,
    build_sample_board,
    ensure_supported_queen_count,
    known_solutions_for_queen_count,
)
from .db import QueensStore
from .threaded import BenchmarkResult, benchmark_threaded_bounded

router = APIRouter(prefix="/api/sixteen-queens", tags=["sixteen-queens"])
store = QueensStore()


class AnswerPayload(BaseModel):
    player_name: str = Field(min_length=1, max_length=50)
    answer: int = Field(ge=0)
    queen_count: int = Field(default=DEFAULT_QUEEN_COUNT)


def _resolve_queen_count(queen_count: int) -> int:
    try:
        return ensure_supported_queen_count(queen_count)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("")
def page_state(queen_count: int = DEFAULT_QUEEN_COUNT) -> dict:
    queen_count = _resolve_queen_count(queen_count)
    return {
        "board_size": BOARD_SIZE,
        "queen_count": queen_count,
        "solutions": known_solutions_for_queen_count(queen_count),
        "sample_board": build_sample_board(queen_count),
        "dashboard": store.dashboard(queen_count=queen_count, limit=None),
        "supported_queen_counts": list(SUPPORTED_QUEEN_COUNTS),
        "current_round": store.current_round(queen_count),
    }


@router.post("/benchmark")
def benchmark(count: int = 1, queen_count: int = DEFAULT_QUEEN_COUNT) -> dict:
    if count <= 0 or count > 20:
        raise HTTPException(status_code=400, detail="count must be between 1 and 20")
    queen_count = _resolve_queen_count(queen_count)

    last = None
    for _ in range(count):
        round_no = store.next_round(queen_count)
        seq_solutions, seq_time, seq_peak = benchmark_sequential_for_queen_count(queen_count)
        seq = BenchmarkResult("sequential", round_no, seq_solutions, seq_time, seq_peak)
        store.save_round(queen_count, seq, build_sample_board(queen_count))

        thr_solutions, thr_time, thr_peak = benchmark_threaded_bounded(queen_count=queen_count)
        thr = BenchmarkResult("threaded", round_no, thr_solutions, thr_time, thr_peak)
        store.save_round(queen_count, thr, build_sample_board(queen_count))

        last = {"round_no": round_no, "sequential": seq.__dict__, "threaded": thr.__dict__}

    return {"message": f"Recorded {count} round(s)", "last": last, "dashboard": store.dashboard(queen_count=queen_count, limit=None), "queen_count": queen_count}


@router.post("/answer")
def submit_answer(payload: AnswerPayload) -> dict:
    queen_count = _resolve_queen_count(payload.queen_count)
    round_no = store.current_round(queen_count)
    if payload.answer != known_solutions_for_queen_count(queen_count):
        raise HTTPException(status_code=400, detail="Wrong answer")
    if store.is_recognized(round_no, queen_count, payload.answer):
        raise HTTPException(status_code=409, detail="This solution has already been recognized")

    store.save_answer(round_no, queen_count, payload.player_name.strip(), payload.answer)
    return {"message": "Answer saved", "round_no": round_no, "queen_count": queen_count}
