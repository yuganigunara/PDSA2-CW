from __future__ import annotations

import argparse
from datetime import datetime

from .algorithms import Position, solve_backtracking, solve_warnsdorff, validate_path
from .storage import save_winner


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Knight's Tour solver in pure Python")
    parser.add_argument("--size", type=int, default=8, choices=[8, 16], help="Board size")
    parser.add_argument("--start-row", type=int, default=0, help="Start row (0-indexed)")
    parser.add_argument("--start-col", type=int, default=0, help="Start col (0-indexed)")
    parser.add_argument(
        "--solver",
        choices=["warnsdorff", "backtracking"],
        default="warnsdorff",
        help="Solver strategy",
    )
    parser.add_argument("--node-limit", type=int, default=3_500_000, help="Backtracking node limit")
    parser.add_argument("--player", default="Anonymous", help="Player name used for saved results")
    parser.add_argument("--save", action="store_true", help="Save successful tours")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    start = Position(args.start_row, args.start_col)

    if args.solver == "warnsdorff":
        path = solve_warnsdorff(args.size, start)
    else:
        path = solve_backtracking(args.size, start, args.node_limit)

    if path is None:
        print("No complete tour found.")
        return 1

    report = validate_path(args.size, path, start)
    print(f"Valid: {report.valid}")
    print(f"Reason: {report.reason}")
    print(f"Coverage: {report.coverage:.2%}")
    print(f"Moves: {len(path)}")

    if report.valid and args.save:
        save_winner(
            {
                "player": args.player,
                "size": args.size,
                "start": start.label(),
                "pathLength": len(path),
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "sequence": [f"{p.row + 1},{p.col + 1}" for p in path],
            }
        )
        print("Winner record saved.")

    return 0 if report.valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
