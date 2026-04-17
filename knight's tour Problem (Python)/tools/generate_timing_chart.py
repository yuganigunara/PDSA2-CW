from __future__ import annotations

import argparse
import csv
import random
import sys
import time
from dataclasses import dataclass
from pathlib import Path

# Ensure local backend package is importable when script is run from project root.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_PATH = PROJECT_ROOT / "backend"
if str(BACKEND_PATH) not in sys.path:
    sys.path.insert(0, str(BACKEND_PATH))

from knighttour.algorithms import Position, solve_backtracking, solve_warnsdorff  # noqa: E402


@dataclass
class RoundTiming:
    round_no: int
    start_row: int
    start_col: int
    warnsdorff_ms: float
    backtracking_ms: float


def run_benchmark(rounds: int = 20, board_size: int = 8, seed: int = 42) -> list[RoundTiming]:
    random.seed(seed)
    rows: list[RoundTiming] = []

    attempt = 0
    max_attempts = rounds * 12
    while len(rows) < rounds:
        attempt += 1
        if attempt > max_attempts:
            raise RuntimeError(
                f"Could not collect {rounds} successful rounds in {max_attempts} attempts"
            )

        round_no = len(rows) + 1
        start = Position(random.randrange(board_size), random.randrange(board_size))

        t0 = time.perf_counter()
        w_path = solve_warnsdorff(board_size, start)
        t1 = time.perf_counter()

        t2 = time.perf_counter()
        b_path = solve_backtracking(board_size, start, 4_000_000)
        t3 = time.perf_counter()

        if w_path is None:
            continue
        if b_path is None:
            continue

        rows.append(
            RoundTiming(
                round_no=round_no,
                start_row=start.row + 1,
                start_col=start.col + 1,
                warnsdorff_ms=(t1 - t0) * 1000.0,
                backtracking_ms=(t3 - t2) * 1000.0,
            )
        )

    return rows


def save_csv(rows: list[RoundTiming], out_csv: Path) -> None:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["round", "start_row", "start_col", "warnsdorff_ms", "backtracking_ms"])
        for r in rows:
            writer.writerow(
                [
                    r.round_no,
                    r.start_row,
                    r.start_col,
                    f"{r.warnsdorff_ms:.3f}",
                    f"{r.backtracking_ms:.3f}",
                ]
            )


def save_svg_chart(rows: list[RoundTiming], out_svg: Path, board_size: int, rounds_target: int) -> None:
    out_svg.parent.mkdir(parents=True, exist_ok=True)

    width = 1200
    height = 620
    margin_left = 80
    margin_right = 40
    margin_top = 60
    margin_bottom = 80

    plot_width = width - margin_left - margin_right
    plot_height = height - margin_top - margin_bottom

    rounds = [r.round_no for r in rows]
    warn = [r.warnsdorff_ms for r in rows]
    back = [r.backtracking_ms for r in rows]
    y_max = max(max(warn), max(back))
    y_max = max(1.0, y_max * 1.1)

    def sx(x: float) -> float:
        if len(rounds) == 1:
            return margin_left + plot_width / 2
        return margin_left + ((x - 1) / (len(rounds) - 1)) * plot_width

    def sy(y: float) -> float:
        return margin_top + (1.0 - y / y_max) * plot_height

    def polyline(values: list[float]) -> str:
        pts = [f"{sx(i + 1):.2f},{sy(v):.2f}" for i, v in enumerate(values)]
        return " ".join(pts)

    y_ticks = 6
    y_grid = []
    y_labels = []
    for i in range(y_ticks + 1):
        yv = y_max * (i / y_ticks)
        ypix = sy(yv)
        y_grid.append(f'<line x1="{margin_left}" y1="{ypix:.2f}" x2="{width - margin_right}" y2="{ypix:.2f}" stroke="#e6ecf3" stroke-width="1" />')
        y_labels.append(
            f'<text x="{margin_left - 10}" y="{ypix + 5:.2f}" text-anchor="end" font-size="12" fill="#4f5d75">{yv:.1f}</text>'
        )

    x_ticks = []
    x_labels = []
    for r in rounds:
        xpix = sx(r)
        x_ticks.append(f'<line x1="{xpix:.2f}" y1="{height - margin_bottom}" x2="{xpix:.2f}" y2="{height - margin_bottom + 6}" stroke="#4f5d75" stroke-width="1" />')
        x_labels.append(
            f'<text x="{xpix:.2f}" y="{height - margin_bottom + 24}" text-anchor="middle" font-size="11" fill="#4f5d75">{r}</text>'
        )

    warn_line = polyline(warn)
    back_line = polyline(back)

    warn_dots = "\n".join(
        f'<circle cx="{sx(i + 1):.2f}" cy="{sy(v):.2f}" r="3.2" fill="#00a896" />' for i, v in enumerate(warn)
    )
    back_dots = "\n".join(
        f'<circle cx="{sx(i + 1):.2f}" cy="{sy(v):.2f}" r="3.2" fill="#ef476f" />' for i, v in enumerate(back)
    )

    svg = f"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"{width}\" height=\"{height}\" viewBox=\"0 0 {width} {height}\">
  <rect x=\"0\" y=\"0\" width=\"{width}\" height=\"{height}\" fill=\"#f8fbff\" />
    <text x=\"{width / 2}\" y=\"34\" text-anchor=\"middle\" font-size=\"22\" font-weight=\"700\" fill=\"#1d3557\">Knight's Tour Solver Timing Over {rounds_target} Rounds</text>
    <text x=\"{width / 2}\" y=\"54\" text-anchor=\"middle\" font-size=\"12\" fill=\"#4f5d75\">Board size: {board_size}x{board_size} | Same random start used for both algorithms in each round</text>

  {' '.join(y_grid)}
  {' '.join(y_labels)}

  <line x1=\"{margin_left}\" y1=\"{height - margin_bottom}\" x2=\"{width - margin_right}\" y2=\"{height - margin_bottom}\" stroke=\"#4f5d75\" stroke-width=\"1.5\" />
  <line x1=\"{margin_left}\" y1=\"{margin_top}\" x2=\"{margin_left}\" y2=\"{height - margin_bottom}\" stroke=\"#4f5d75\" stroke-width=\"1.5\" />

  {' '.join(x_ticks)}
  {' '.join(x_labels)}

  <polyline points=\"{warn_line}\" fill=\"none\" stroke=\"#00a896\" stroke-width=\"2.6\" />
  <polyline points=\"{back_line}\" fill=\"none\" stroke=\"#ef476f\" stroke-width=\"2.6\" />

  {warn_dots}
  {back_dots}

  <rect x=\"{width - 290}\" y=\"{margin_top + 10}\" width=\"230\" height=\"66\" rx=\"8\" fill=\"#ffffff\" stroke=\"#d6e2f0\" />
  <line x1=\"{width - 270}\" y1=\"{margin_top + 30}\" x2=\"{width - 235}\" y2=\"{margin_top + 30}\" stroke=\"#00a896\" stroke-width=\"3\" />
  <text x=\"{width - 225}\" y=\"{margin_top + 34}\" font-size=\"12\" fill=\"#1d3557\">Warnsdorff</text>
  <line x1=\"{width - 270}\" y1=\"{margin_top + 54}\" x2=\"{width - 235}\" y2=\"{margin_top + 54}\" stroke=\"#ef476f\" stroke-width=\"3\" />
  <text x=\"{width - 225}\" y=\"{margin_top + 58}\" font-size=\"12\" fill=\"#1d3557\">Backtracking</text>

  <text x=\"{width / 2}\" y=\"{height - 20}\" text-anchor=\"middle\" font-size=\"13\" fill=\"#1d3557\">Round number</text>
  <text transform=\"translate(24 {height / 2}) rotate(-90)\" text-anchor=\"middle\" font-size=\"13\" fill=\"#1d3557\">Execution time (ms)</text>
</svg>
"""
    out_svg.write_text(svg, encoding="utf-8")


def save_summary(
    rows: list[RoundTiming],
    out_md: Path,
    board_size: int,
    rounds_target: int,
    csv_name: str,
    svg_name: str,
) -> None:
    warn = [r.warnsdorff_ms for r in rows]
    back = [r.backtracking_ms for r in rows]

    warn_avg = sum(warn) / len(warn)
    back_avg = sum(back) / len(back)
    speedup = back_avg / warn_avg if warn_avg > 0 else 0.0

    lines = [
        f"# Knight's Tour {rounds_target}-Round Timing Report ({board_size}x{board_size})",
        "",
        f"## iv. Chart Containing Time Taken Per Algorithm ({rounds_target} Rounds)",
        "",
        f"- Chart file: reports/{svg_name}",
        f"- Raw data: reports/{csv_name}",
        "",
        f"- Average Warnsdorff time: {warn_avg:.3f} ms",
        f"- Average Backtracking time: {back_avg:.3f} ms",
        f"- Relative factor (Backtracking / Warnsdorff): {speedup:.2f}x",
        "",
        "## v. Video Clip Link Demonstrating Rounds & Time Taken",
        "",
        "- Video link: REPLACE_WITH_YOUR_VIDEO_LINK",
        f"- Suggested title: Knight's Tour {board_size}x{board_size} {rounds_target} Rounds Algorithm Timing Demo",
        "",
        "### Suggested video flow",
        "1. Show benchmark command execution in terminal.",
        "2. Show generated CSV and SVG chart files.",
        "3. Briefly explain average timings and which algorithm is faster.",
    ]

    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _base_stem(file_path: Path) -> str:
    name = file_path.name
    for suffix in ("_timing.csv", "_timing.svg", "_report.md"):
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return file_path.stem


def prune_old_output_sets(reports_dir: Path, keep_latest_sets: int) -> list[Path]:
    if keep_latest_sets <= 0:
        return []

    files = [
        p
        for p in reports_dir.glob("knight_tour_*")
        if p.name.endswith("_timing.csv") or p.name.endswith("_timing.svg") or p.name.endswith("_report.md")
    ]
    if not files:
        return []

    stems_with_time: dict[str, float] = {}
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

    deleted: list[Path] = []
    for p in files:
        stem = _base_stem(p)
        if stem in keep_stems:
            continue
        p.unlink(missing_ok=True)
        deleted.append(p)
    return deleted


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Knight's Tour timing chart")
    parser.add_argument("--size", type=int, choices=[8, 16], default=8, help="Board size to benchmark")
    parser.add_argument("--rounds", type=int, default=20, help="Number of successful rounds to record")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducible starts")
    parser.add_argument(
        "--tag",
        type=str,
        default="",
        help="Optional suffix for output filenames (example: yusha or collaborator)",
    )
    parser.add_argument(
        "--keep-latest-sets",
        type=int,
        default=2,
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
    board_size = int(args.size)
    rows = run_benchmark(rounds=rounds_target, board_size=board_size, seed=int(args.seed))

    reports_dir = PROJECT_ROOT / "reports"
    stem = f"knight_tour_{board_size}x{board_size}_{rounds_target}_rounds"
    tag = args.tag.strip().replace(" ", "_")
    if tag:
        stem = f"{stem}_{tag}"

    csv_path = reports_dir / f"{stem}_timing.csv"
    svg_path = reports_dir / f"{stem}_timing.svg"
    report_path = reports_dir / f"{stem}_report.md"

    save_csv(rows, csv_path)
    save_svg_chart(rows, svg_path, board_size=board_size, rounds_target=rounds_target)
    save_summary(
        rows,
        report_path,
        board_size=board_size,
        rounds_target=rounds_target,
        csv_name=csv_path.name,
        svg_name=svg_path.name,
    )

    deleted_files: list[Path] = []
    if not args.no_prune:
        deleted_files = prune_old_output_sets(reports_dir, keep_latest_sets=max(1, args.keep_latest_sets))

    print(f"Created: {csv_path}")
    print(f"Created: {svg_path}")
    print(f"Created: {report_path}")
    if deleted_files:
        print(f"Deleted old files: {len(deleted_files)}")


if __name__ == "__main__":
    main()
