from pathlib import Path

from app.config import EDGES
from app.main import create_app


def _db_path(tmp_path: Path) -> Path:
    return tmp_path / "traffic_test.db"


def test_benchmark_endpoint_returns_20_rounds(tmp_path):
    app = create_app(_db_path(tmp_path))

    with app.test_client() as client:
        response = client.get("/api/benchmark")

    assert response.status_code == 200
    payload = response.get_json()

    assert payload["rounds"] == 20
    assert len(payload["labels"]) == 20
    assert len(payload["fordFulkersonMs"]) == 20
    assert len(payload["edmondsKarpMs"]) == 20
    assert payload["averageFordFulkersonMs"] >= 0
    assert payload["averageEdmondsKarpMs"] >= 0


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
