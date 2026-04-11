# Traffic Simulation Max-Flow Game

A mini game where each round generates random road capacities and the player guesses the maximum flow from **A** to **T**.

## Features

- Fixed 9-node traffic network: `A, B, C, D, E, F, G, H, T`
- Random capacities per round (`5-15` vehicles/min)
- Two max-flow solvers:
  - Ford-Fulkerson
  - Edmonds-Karp
- Win/Lose/Draw outcome (`draw` if within ±2)
- SQLite persistence for:
  - round stats
  - player wins (name + answer)
- Leaderboard endpoint and UI section
- Unit tests for max-flow correctness

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

Open:

- http://127.0.0.1:5000

## Test

```bash
pytest -q
```

## Project structure

- `app/algorithms.py` - max-flow implementations
- `app/main.py` - Flask routes and game flow
- `app/storage.py` - SQLite access layer
- `app/templates/index.html` - UI shell
- `app/static/app.js` - graph rendering + frontend gameplay
- `tests/test_algorithms.py` - algorithm unit tests
