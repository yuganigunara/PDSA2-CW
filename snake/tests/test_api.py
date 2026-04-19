from pathlib import Path

from fastapi.testclient import TestClient

from snake_ladder.api import create_app
from snake_ladder.database import ResultRepository


def _client(tmp_path: Path) -> TestClient:
    repo = ResultRepository(str(tmp_path / "snake_test.db"))
    app = create_app(repository=repo)
    return TestClient(app)


def test_health_route(tmp_path: Path) -> None:
    client = _client(tmp_path)

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_round_route_returns_payload(tmp_path: Path) -> None:
    client = _client(tmp_path)

    response = client.post("/api/round", json={"player_name": " Alice ", "board_size": 6})

    assert response.status_code == 200
    payload = response.json()
    assert payload["player_name"] == "Alice"
    assert payload["board"]["size"] == 6
    assert payload["board"]["goal"] == 36
    assert len(payload["options"]) == 3
    assert payload["correct_answer"] in payload["options"]
    assert payload["outcome"] in {"PENDING", "DRAW"}


def test_results_route_saves_correct_answer_and_returns_recent_rows(tmp_path: Path) -> None:
    client = _client(tmp_path)
    round_response = client.post("/api/round", json={"player_name": "Alice", "board_size": 6})
    round_payload = round_response.json()

    save_response = client.post(
        "/api/results",
        json={
            "player_name": round_payload["player_name"],
            "answer": round_payload["correct_answer"],
            "correct_answer": round_payload["correct_answer"],
            "outcome": round_payload["outcome"],
            "bfs_time_ns": round_payload["bfs"]["time_ns"],
            "dp_time_ns": round_payload["dp"]["time_ns"],
            "board_size": round_payload["board"]["size"],
            "ladders": round_payload["board"]["ladders"],
            "snakes": round_payload["board"]["snakes"],
        },
    )

    assert save_response.status_code == 200
    saved_payload = save_response.json()
    assert saved_payload["player_name"] == "Alice"
    assert saved_payload["answer"] == round_payload["correct_answer"]

    rows_response = client.get("/api/results")
    assert rows_response.status_code == 200
    rows = rows_response.json()
    assert len(rows) == 1
    assert rows[0]["player_name"] == "Alice"


def test_results_route_rejects_incorrect_answers(tmp_path: Path) -> None:
    client = _client(tmp_path)

    response = client.post(
        "/api/results",
        json={
            "player_name": "Alice",
            "answer": 2,
            "correct_answer": 3,
            "outcome": "PENDING",
            "bfs_time_ns": 10,
            "dp_time_ns": 12,
            "board_size": 6,
            "ladders": {},
            "snakes": {},
        },
    )

    assert response.status_code == 400


def test_results_route_rejects_draw_round_save(tmp_path: Path) -> None:
    client = _client(tmp_path)

    response = client.post(
        "/api/results",
        json={
            "player_name": "Alice",
            "answer": 4,
            "correct_answer": 4,
            "outcome": "DRAW",
            "bfs_time_ns": 10,
            "dp_time_ns": 12,
            "board_size": 6,
            "ladders": {},
            "snakes": {},
        },
    )

    assert response.status_code == 400


def test_benchmark_route_returns_samples(tmp_path: Path) -> None:
    client = _client(tmp_path)

    response = client.get("/api/benchmark", params={"rounds": 3, "board_size": 6})

    assert response.status_code == 200
    payload = response.json()
    assert payload["rounds"] == 3
    assert payload["board_size"] == 6
    assert len(payload["samples"]) == 3