from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "traffic_game.db"
DRAW_MARGIN = 2

NODES = ["A", "B", "C", "D", "E", "F", "G", "H", "T"]
EDGES = [
    ("A", "B"),
    ("A", "C"),
    ("A", "D"),
    ("B", "E"),
    ("B", "F"),
    ("C", "E"),
    ("C", "F"),
    ("D", "F"),
    ("D", "H"),
    ("E", "G"),
    ("E", "H"),
    ("F", "G"),
    ("F", "H"),
    ("G", "T"),
    ("H", "T"),
]
