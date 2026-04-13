import unittest
from pathlib import Path
from unittest.mock import patch
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from knighttour.algorithms import Position, solve_warnsdorff
from knighttour.api import app


class APITests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = app.test_client()

    def test_solve_rejects_non_assignment_board_size(self) -> None:
        response = self.client.post(
            "/api/solve",
            json={
                "size": 6,
                "solver": "warnsdorff",
                "startRow": 0,
                "startCol": 0,
            },
        )

        self.assertEqual(response.status_code, 400)
        payload = response.get_json() or {}
        self.assertEqual(payload.get("error"), "Invalid board size")

    def test_winner_rejects_empty_path(self) -> None:
        response = self.client.post(
            "/api/winners",
            json={
                "player": "Tester",
                "size": 8,
                "path": [],
            },
        )

        self.assertEqual(response.status_code, 400)
        payload = response.get_json() or {}
        self.assertIn("Path is required", payload.get("error", ""))

    def test_winner_rejects_invalid_tour_path(self) -> None:
        response = self.client.post(
            "/api/winners",
            json={
                "player": "Tester",
                "size": 8,
                "path": [[0, 0], [1, 1]],
            },
        )

        self.assertEqual(response.status_code, 400)
        payload = response.get_json() or {}
        self.assertIn("Invalid winner path", payload.get("error", ""))

    def test_winner_accepts_valid_complete_tour(self) -> None:
        path = solve_warnsdorff(8, Position(0, 0))
        self.assertIsNotNone(path)
        payload_path = [[step.row, step.col] for step in (path or [])]

        with patch("knighttour.api.save_winner") as mock_save_winner:
            response = self.client.post(
                "/api/winners",
                json={
                    "player": "Tester",
                    "size": 8,
                    "path": payload_path,
                },
            )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(mock_save_winner.called)


if __name__ == "__main__":
    unittest.main()
