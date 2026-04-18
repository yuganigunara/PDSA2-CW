from __future__ import annotations

import argparse
import csv
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.main import _random_capacities, _timed_max_flow

@dataclass
class RoundTiming:
    round_no: int
    ford_fulkerson_ms: float
    edmonds_karp_ms: float
    correct_max_flow: int

def run_benchmark(rounds: int = 20) -> list[RoundTiming]:
    rows: list[RoundTiming] = []
    for i in range(1, rounds + 1):
        capacities = _random_capacities()
        correct, ff_ms, ek_ms = _timed_max_flow(capacities)
        rows.append(RoundTiming(
            round_no=i,
            ford_fulkerson_ms=ff_ms,
            edmonds_karp_ms=ek_ms,
            correct_max_flow=correct
        ))
    return rows

def save_csv(rows: list[RoundTiming], out_csv: Path) -> None:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["round", "ford_fulkerson_ms", "edmonds_karp_ms", "correct_max_flow"])
        for r in rows:
            writer.writerow([
                r.round_no,
                f"{r.ford_fulkerson_ms:.4f}",
                f"{r.edmonds_karp_ms:.4f}",
                r.correct_max_flow
            ])

def save_svg_chart(rows: list[RoundTiming], out_svg: Path, rounds_target: int) -> None:
    out_svg.parent.mkdir(parents=True, exist_ok=True)
    rounds = [r.round_no for r in rows]
    ff = [r.ford_fulkerson_ms for r in rows]
    ek = [r.edmonds_karp_ms for r in rows]
    plt.figure(figsize=(10,6))
    plt.plot(rounds, ff, marker='o', label="Ford-Fulkerson (ms)")
    plt.plot(rounds, ek, marker='s', label="Edmonds-Karp (ms)")
    plt.xlabel("Round")
    plt.ylabel("Time (ms)")
    plt.title(f"Traffic Simulation: Algorithm Timing per Round ({rounds_target} Rounds)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(out_svg)
    plt.close()

def _base_stem(file_path: Path) -> str:
    name = file_path.name
    for suffix in (".csv", ".svg"):
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return file_path.stem

def prune_old_output_sets(reports_dir: Path, keep_latest_sets: int) -> List[Path]:
    if keep_latest_sets <= 0:
        return []
    files = [
        p
        for p in reports_dir.glob("traffic_timing_*.csv")
    ] + [
        p
        for p in reports_dir.glob("traffic_timing_*.svg")
    ]
    if not files:
        return []
    stems_with_time = {}
    for p in files:
        stem = _base_stem(p)
        mtime = p.stat().st_mtime
        prev = stems_with_time.get(stem)
        if prev is None or mtime > prev:
            stems_with_time[stem] = mtime
    keep_stems = {
        stem
        for stem, _ in sorted(stems_with_time.items(), key=lambda item: item[1], reverse=True)[:keep_latest_sets]
    }
    deleted = []
    for p in files:
        stem = _base_stem(p)
        if stem in keep_stems:
            continue
        p.unlink(missing_ok=True)
        deleted.append(p)
    return deleted

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Traffic Simulation timing chart")
    parser.add_argument("--rounds", type=int, default=20, help="Number of rounds to run")
    parser.add_argument("--tag", type=str, default="", help="Tag for output files")
    parser.add_argument(
        "--keep-latest-sets",
        type=int,
        default=1,
        help="Keep only latest N generated chart sets in reports directory",
    )
    parser.add_argument(
        "--no-prune",
        action="store_true",
        help="Disable deletion of older generated chart sets",
    )
    return parser.parse_args()

def main() -> None:
    args = parse_args()
    rounds_target = max(1, int(args.rounds))
    tag = args.tag.strip().replace(" ", "_")
    reports_dir = PROJECT_ROOT / "reports"
    stem = f"traffic_timing_{rounds_target}_rounds"
    if tag:
        stem = f"{stem}_{tag}"
    csv_path = reports_dir / f"{stem}.csv"
    svg_path = reports_dir / f"{stem}.svg"
    rows = run_benchmark(rounds=rounds_target)
    save_csv(rows, csv_path)
    save_svg_chart(rows, svg_path, rounds_target=rounds_target)
    deleted_files: List[Path] = []
    if not args.no_prune:
        deleted_files = prune_old_output_sets(reports_dir, keep_latest_sets=max(1, args.keep_latest_sets))
    print(f"Created: {csv_path}")
    print(f"Created: {svg_path}")
    if deleted_files:
        print(f"Deleted old files: {len(deleted_files)}")

if __name__ == "__main__":
    main()