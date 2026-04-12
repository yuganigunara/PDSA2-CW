import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from knighttour.storage import get_winners, save_winner


class StorageTests(unittest.TestCase):
    def test_save_and_get_winner_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_file = Path(tmp) / "winners.db"
            save_winner(
                {
                    "player": "Tester",
                    "size": 8,
                    "start": "(1, 1)",
                    "pathLength": 64,
                    "timestamp": "2026-04-11T12:00:00",
                    "sequence": ["1,1", "3,2"],
                },
                db_file,
            )

            winners = get_winners(db_file)
            self.assertEqual(len(winners), 1)
            self.assertEqual(winners[0]["player"], "Tester")
            self.assertEqual(winners[0]["pathLength"], 64)
            self.assertEqual(winners[0]["sequence"], ["1,1", "3,2"])

    def test_keeps_latest_fifteen_records(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_file = Path(tmp) / "winners.db"
            for i in range(20):
                save_winner(
                    {
                        "player": f"P{i}",
                        "size": 8,
                        "start": "(1, 1)",
                        "pathLength": 64,
                        "timestamp": f"2026-04-11T12:00:{i:02d}",
                        "sequence": [],
                    },
                    db_file,
                )

            winners = get_winners(db_file)
            self.assertEqual(len(winners), 15)
            self.assertEqual(winners[0]["player"], "P19")
            self.assertEqual(winners[-1]["player"], "P5")


if __name__ == "__main__":
    unittest.main()
