import sqlite3
from pathlib import Path

from backend.app.config import EDGES
from backend.app.main import create_app


def _db_path(tmp_path: Path) -> Path:
    return tmp_path / "traffic_test.db"


def test_new_round_generates_required_edges_within_range(tmp_path: Path):
    app = create_app(_db_path(tmp_path))
    client = app.test_client()

    response = client.post("/api/new-round")
    assert response.status_code == 200

    payload = response.get_json()
    capacities = payload["capacities"]

    expected_keys = {f"{u}->{v}" for u, v in EDGES}
    assert set(capacities.keys()) == expected_keys
    assert all(5 <= int(value) <= 15 for value in capacities.values())


def test_submit_validates_negative_answer(tmp_path: Path):
    app = create_app(_db_path(tmp_path))
    client = app.test_client()

    response = client.post(
        "/api/submit",
        json={"roundId": 1, "answer": -1, "playerName": "Tester"},
    )

    assert response.status_code == 400
    payload = response.get_json()
    assert "non-negative" in payload["error"]


def test_submit_validates_player_name_length(tmp_path: Path):
    app = create_app(_db_path(tmp_path))
    client = app.test_client()

    response = client.post(
        "/api/submit",
        json={"roundId": 1, "answer": 10, "playerName": "x" * 41},
    )

    assert response.status_code == 400
    payload = response.get_json()
    assert "40" in payload["error"]


def test_submit_returns_not_found_for_missing_round(tmp_path: Path):
    app = create_app(_db_path(tmp_path))
    client = app.test_client()

    response = client.post(
        "/api/submit",
        json={"roundId": 999, "answer": 10, "playerName": "Tester"},
    )

    assert response.status_code == 404


def test_submit_saves_win_and_returns_timing_payload(tmp_path: Path):
    db_path = _db_path(tmp_path)
    app = create_app(db_path)
    client = app.test_client()

    round_response = client.post("/api/new-round")
    assert round_response.status_code == 200

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        round_row = conn.execute(
            "SELECT id, correct_max_flow FROM rounds ORDER BY id DESC LIMIT 1"
        ).fetchone()

    assert round_row is not None

    submit_response = client.post(
        "/api/submit",
        json={
            "roundId": round_row["id"],
            "answer": round_row["correct_max_flow"],
            "playerName": "Tester",
        },
    )

    assert submit_response.status_code == 200
    submit_payload = submit_response.get_json()
    assert submit_payload["result"] == "win"
    assert submit_payload["correctMaxFlow"] == round_row["correct_max_flow"]
    assert submit_payload["fordFulkersonMs"] >= 0
    assert submit_payload["edmondsKarpMs"] >= 0

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        win_row = conn.execute(
            "SELECT player_name, answer, round_id FROM wins ORDER BY id DESC LIMIT 1"
        ).fetchone()

    assert win_row is not None
    assert win_row["player_name"] == "Tester"
    assert win_row["answer"] == round_row["correct_max_flow"]
    assert win_row["round_id"] == round_row["id"]
