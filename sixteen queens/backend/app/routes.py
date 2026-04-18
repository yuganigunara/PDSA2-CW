from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .backtracking import KNOWN_SOLUTIONS, QUEENS_SIZE, benchmark_sequential, build_sample_board
from .db import QueensStore
from .threaded import BenchmarkResult, benchmark_threaded_bounded

router = APIRouter(prefix="/api/sixteen-queens", tags=["sixteen-queens"])
store = QueensStore()


class AnswerPayload(BaseModel):
    player_name: str = Field(min_length=1, max_length=50)
    answer: int = Field(ge=0)


@router.get("")
def page_state() -> dict:
    return {
        "size": QUEENS_SIZE,
        "solutions": KNOWN_SOLUTIONS,
        "sample_board": build_sample_board(),
        "dashboard": store.dashboard(limit=None),
    }


@router.post("/benchmark")
def benchmark(count: int = 1) -> dict:
    if count <= 0 or count > 20:
        raise HTTPException(status_code=400, detail="count must be between 1 and 20")

    last = None
    for _ in range(count):
        round_no = store.next_round()
        seq_solutions, seq_time, seq_peak = benchmark_sequential()
        seq = BenchmarkResult("sequential", round_no, seq_solutions, seq_time, seq_peak)
        store.save_round(seq, build_sample_board())

        thr_solutions, thr_time, thr_peak = benchmark_threaded_bounded()
        thr = BenchmarkResult("threaded", round_no, thr_solutions, thr_time, thr_peak)
        store.save_round(thr, build_sample_board())

        last = {"round_no": round_no, "sequential": seq.__dict__, "threaded": thr.__dict__}

    return {"message": f"Recorded {count} round(s)", "last": last, "dashboard": store.dashboard(limit=None)}


@router.post("/answer")
def submit_answer(payload: AnswerPayload) -> dict:
    round_no = store.current_round()
    if payload.answer != KNOWN_SOLUTIONS:
        raise HTTPException(status_code=400, detail="Wrong answer")
    if store.is_recognized(round_no, payload.answer):
        raise HTTPException(status_code=409, detail="This solution has already been recognized")

    store.save_answer(round_no, payload.player_name.strip(), payload.answer)
    return {"message": "Answer saved", "round_no": round_no}
