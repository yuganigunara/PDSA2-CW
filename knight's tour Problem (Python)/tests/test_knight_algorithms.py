import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from knighttour.algorithms import Position, is_knight_move, solve_backtracking, solve_warnsdorff, validate_path


class KnightAlgorithmTests(unittest.TestCase):
    def test_is_knight_move_validates_l_shape(self) -> None:
        self.assertTrue(is_knight_move(Position(0, 0), Position(2, 1)))
        self.assertTrue(is_knight_move(Position(4, 4), Position(5, 6)))
        self.assertFalse(is_knight_move(Position(0, 0), Position(1, 1)))

    def test_warnsdorff_returns_valid_full_tour_on_8x8(self) -> None:
        start = Position(0, 0)
        path = solve_warnsdorff(8, start)
        self.assertIsNotNone(path, "Warnsdorff should produce a path")
        report = validate_path(8, path or [], start)
        self.assertTrue(report.valid, report.reason)
        self.assertEqual(len(path or []), 64)

    def test_backtracking_returns_valid_full_tour_on_8x8(self) -> None:
        start = Position(0, 0)
        path = solve_backtracking(8, start, 4_000_000)
        self.assertIsNotNone(path, "Backtracking should produce a path")
        report = validate_path(8, path or [], start)
        self.assertTrue(report.valid, report.reason)

    def test_validate_path_catches_repeated_squares(self) -> None:
        start = Position(0, 0)
        bad_path = [
            Position(0, 0),
            Position(2, 1),
            Position(0, 0),
        ]
        report = validate_path(8, bad_path, start)
        self.assertFalse(report.valid)
        self.assertIn("Square repeated", report.reason)


if __name__ == "__main__":
    unittest.main()
