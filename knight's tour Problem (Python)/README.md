# Knight's Tour in Python

Pure Python implementation of Knight's Tour logic, solvers, persistence, and tests.

## Features

- Board sizes: 8x8 and 16x16
- Menu option: Knight's Tour Problem
- Knight move validation and path validation
- Warnsdorff solver
- Backtracking solver with configurable node limit
- Random starting position for each game round
- Player answer input through GUI (manual move sequence)
- Win/lose/draw game UI feedback
- Winner persistence to local SQLite database
- Python unit tests

## Requirements

- Python 3.10+

## Install

```bash
python3 -m pip install -e .
```

## Run

```bash
python3 -m knighttour.app --size 8 --start-row 0 --start-col 0 --solver warnsdorff
```

## Frontend

### React browser UI

A modern React frontend is available in [`frontend/`](frontend/).

```bash
cd frontend
npm install
npm run dev
```

### Tkinter desktop UI

The original desktop app is still available if you want the Python GUI:

```bash
python3 -m knighttour.gui
```

Or after install:

```bash
knights-tour-gui
```

Inside the app, open the Game menu and select Knight's Tour Problem.

Optional winner save:

```bash
python3 -m knighttour.app --size 8 --start-row 0 --start-col 0 --solver backtracking --save --player "Player 1"
```

## Test

```bash
python3 -m unittest discover -s tests -p "test_*.py"
```

Includes tests for:
- Algorithms and path validation
- Database persistence for winners

## Project Structure

- backend/knighttour/algorithms.py - knight tour algorithms and validation
- backend/knighttour/storage.py - winner persistence layer
- backend/knighttour/app.py - CLI entry point
- frontend/src/App.tsx - React page coordinator
- frontend/src/components/Board.tsx - board rendering and move highlighting
- frontend/src/components/SetupPanel.tsx - gameplay controls and settings
- frontend/src/components/StatusPanel.tsx - status, move history, and saved tours
- frontend/src/knightTour.ts - shared browser-side solver logic
- tests/test_knight_algorithms.py - unit tests
- tests/test_storage.py - storage unit tests
