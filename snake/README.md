# Snake and Ladder Coursework

## Features

- Board size `N x N`, with `N` validated in range 6 to 12.
- Random board generation each round with:
  - `N-2` ladders
  - `N-2` snakes
- Non-overlapping snake and ladder positions.
- Two minimum-throw algorithms:
  - BFS (shortest path)
  - DP (iterative relaxation)
- Performance timing for BFS and DP.
- Multiple-choice gameplay (3 options).
- WIN/LOSE/DRAW result screen.
- SQLite persistence for correct answers only.
- Unit tests for algorithms, validations, and exceptions.

## Run

```bash
python -m pip install -r requirements.txt
python main.py
```

`main.py` now starts the desktop GUI by default.

GUI also includes a `Sixteen Queens Puzzle` option.

If you want terminal mode instead:

```bash
python main.py --mode cli
```

In CLI mode, menu options are:

- Snake and Ladder round
- Sixteen Queens puzzle (sequential vs threaded benchmark, player answer, DB save)
- Exit

## Test

```bash
pytest -q
```
