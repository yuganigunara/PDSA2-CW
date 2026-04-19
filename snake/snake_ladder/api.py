from __future__ import annotations

import random

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field, field_validator

from snake_ladder.algorithms import timed_bfs, timed_dp
from snake_ladder.board import (
    BoardGenerationError,
    BoardSetup,
    ValidationError,
    generate_random_board,
    validate_board_size,
)
from snake_ladder.database import DatabaseError, ResultRepository


class RoundRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    player_name: str = Field(min_length=1, max_length=50)
    board_size: int = Field(ge=6, le=12)

    @field_validator("player_name")
    @classmethod
    def _strip_player_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Player name is required.")
        return cleaned


class SaveResultRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    player_name: str = Field(min_length=1, max_length=50)
    answer: int = Field(ge=1)
    correct_answer: int = Field(ge=1)
    outcome: str = Field(pattern="^(PENDING|DRAW)$")
    bfs_time_ns: int = Field(ge=0)
    dp_time_ns: int = Field(ge=0)
    board_size: int = Field(ge=6, le=12)
    ladders: dict[int, int]
    snakes: dict[int, int]

    @field_validator("player_name")
    @classmethod
    def _strip_player_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Player name is required.")
        return cleaned


class BoardPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    size: int
    ladders: dict[int, int]
    snakes: dict[int, int]
    goal: int
    jumps: dict[int, int]


class AlgorithmPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    minimum_throws: int
    time_ns: int


class RoundResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    player_name: str
    board: BoardPayload
    bfs: AlgorithmPayload
    dp: AlgorithmPayload
    options: list[int]
    correct_answer: int
    outcome: str


class ResultRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    player_name: str
    answer: int
    bfs_time_ns: int
    dp_time_ns: int
    board_size: int
    ladders: dict[int, int]
    snakes: dict[int, int]
    created_at: str


class BenchmarkSample(BaseModel):
    model_config = ConfigDict(extra="forbid")

    round_number: int
    bfs_time_ns: int
    dp_time_ns: int
    bfs_ms: float
    dp_ms: float


class BenchmarkResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rounds: int
    board_size: int
    average_bfs_ms: float
    average_dp_ms: float
    samples: list[BenchmarkSample]


class PlayerRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    player_id: int
    player_name: str
    created_at: str


class GameRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    game_id: int
    player_id: int
    board_size: int
    correct_answer: int
    player_answer: int
    is_correct: int
    created_at: str


class GameJumpRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    jump_id: int
    game_id: int
    jump_type: str
    start_cell: int
    end_cell: int


class AlgorithmRunRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: int
    game_id: int
    algorithm_name: str
    minimum_throws: int
    time_ns: int


class DatabaseSnapshotResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    players: list[PlayerRow]
    games: list[GameRow]
    game_jumps: list[GameJumpRow]
    algorithm_runs: list[AlgorithmRunRow]


def ns_to_ms(value: float | int) -> float:
    return round(float(value) / 1_000_000, 3)


def build_board_payload(board: BoardSetup) -> BoardPayload:
    return BoardPayload(
        size=board.size,
        ladders=board.ladders,
        snakes=board.snakes,
        goal=board.goal,
        jumps=board.jumps,
    )


def build_answer_options(correct_answer: int, rng: random.Random | None = None) -> list[int]:
    rng = rng or random.Random()
    options = {correct_answer}
    offset = 1
    while len(options) < 3:
        lower = correct_answer - offset
        upper = correct_answer + offset
        if lower >= 1:
            options.add(lower)
        if len(options) < 3:
            options.add(upper)
        offset += 1
    values = list(options)
    rng.shuffle(values)
    return values


def build_round_payload(player_name: str, board_size: int, *, rng: random.Random | None = None) -> RoundResponse:
    validate_board_size(board_size)
    rng = rng or random.Random()

    board = generate_random_board(board_size, rng=rng)
    bfs_result = timed_bfs(board)
    dp_result = timed_dp(board)
    correct_answer = bfs_result.minimum_throws
    outcome = "DRAW" if bfs_result.minimum_throws != dp_result.minimum_throws else "PENDING"

    return RoundResponse(
        player_name=player_name,
        board=build_board_payload(board),
        bfs=AlgorithmPayload(minimum_throws=bfs_result.minimum_throws, time_ns=bfs_result.time_ns),
        dp=AlgorithmPayload(minimum_throws=dp_result.minimum_throws, time_ns=dp_result.time_ns),
        options=build_answer_options(correct_answer, rng=rng),
        correct_answer=correct_answer,
        outcome=outcome,
    )


def create_app(repository: ResultRepository | None = None) -> FastAPI:
    app = FastAPI(title="Snake and Ladder Coursework API")
    repo = repository or ResultRepository()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/round", response_model=RoundResponse)
    def round_route(payload: RoundRequest) -> RoundResponse:
        try:
            return build_round_payload(payload.player_name, payload.board_size)
        except (ValidationError, BoardGenerationError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/results", response_model=ResultRow)
    def save_result(payload: SaveResultRequest) -> ResultRow:
        if payload.outcome == "DRAW":
            raise HTTPException(status_code=400, detail="DRAW rounds cannot be saved.")

        if payload.answer != payload.correct_answer:
            raise HTTPException(status_code=400, detail="Only correct answers can be saved.")

        try:
            board = BoardSetup(
                size=payload.board_size,
                ladders=payload.ladders,
                snakes=payload.snakes,
            )
            game_id = repo.save_result(
                player_name=payload.player_name,
                player_answer=payload.answer,
                correct_answer=payload.correct_answer,
                bfs_time_ns=payload.bfs_time_ns,
                dp_time_ns=payload.dp_time_ns,
                board=board,
            )
            row = repo.get_result_by_game_id(game_id)
            if row is None:
                raise HTTPException(status_code=500, detail="Saved result could not be retrieved.")
        except ValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except DatabaseError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

        return ResultRow(**row)

    @app.get("/api/results", response_model=list[ResultRow])
    def get_results(limit: int = Query(default=50, ge=1, le=100)) -> list[ResultRow]:
        try:
            rows = repo.get_recent_results(limit=limit)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except DatabaseError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        return [ResultRow(**row) for row in rows]

    @app.get("/api/database", response_model=DatabaseSnapshotResponse)
    def get_database() -> DatabaseSnapshotResponse:
        try:
            snapshot = repo.get_database_snapshot()
        except DatabaseError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        return DatabaseSnapshotResponse(**snapshot)

    @app.get("/api/benchmark", response_model=BenchmarkResponse)
    def benchmark(
        rounds: int = Query(default=20, ge=1, le=50),
        board_size: int = Query(default=8, ge=6, le=12),
    ) -> BenchmarkResponse:
        try:
            validate_board_size(board_size)
            samples: list[BenchmarkSample] = []
            bfs_total = 0
            dp_total = 0
            for round_number in range(1, rounds + 1):
                board = generate_random_board(board_size)
                bfs_result = timed_bfs(board)
                dp_result = timed_dp(board)
                bfs_total += bfs_result.time_ns
                dp_total += dp_result.time_ns
                samples.append(
                    BenchmarkSample(
                        round_number=round_number,
                        bfs_time_ns=bfs_result.time_ns,
                        dp_time_ns=dp_result.time_ns,
                        bfs_ms=ns_to_ms(bfs_result.time_ns),
                        dp_ms=ns_to_ms(dp_result.time_ns),
                    )
                )
        except (ValidationError, BoardGenerationError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        return BenchmarkResponse(
            rounds=rounds,
            board_size=board_size,
            average_bfs_ms=ns_to_ms(bfs_total / rounds),
            average_dp_ms=ns_to_ms(dp_total / rounds),
            samples=samples,
        )

    return app


app = create_app()