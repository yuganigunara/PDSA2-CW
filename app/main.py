import json
import random
import time
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from app.algorithms import edmonds_karp_max_flow, ford_fulkerson_max_flow
from app.config import DB_PATH, DRAW_MARGIN, EDGES
from app.storage import get_leaderboard, get_round, init_db, save_round, save_win

app = Flask(__name__, template_folder="templates", static_folder="static")


def _random_capacities():
    capacities = {}
    for u, v in EDGES:
        capacities[f"{u}->{v}"] = random.randint(5, 15)
    return capacities


def _to_algo_capacities(capacities):
    return {tuple(edge.split("->")): value for edge, value in capacities.items()}


def _timed_max_flow(capacities):
    algo_caps = _to_algo_capacities(capacities)

    start_ff = time.perf_counter_ns()
    ff_result = ford_fulkerson_max_flow(algo_caps, "A", "T")
    ff_ms = (time.perf_counter_ns() - start_ff) / 1_000_000

    start_ek = time.perf_counter_ns()
    ek_result = edmonds_karp_max_flow(algo_caps, "A", "T")
    ek_ms = (time.perf_counter_ns() - start_ek) / 1_000_000

    if ff_result != ek_result:
        raise ValueError("Algorithms returned different max-flow values")

    return ff_result, ff_ms, ek_ms


@app.route("/")
def index():
    return render_template("index.html")


@app.post("/api/new-round")
def new_round():
    capacities = _random_capacities()
    correct, ff_ms, ek_ms = _timed_max_flow(capacities)
    round_id = save_round(DB_PATH, capacities, correct, ff_ms, ek_ms)

    return jsonify(
        {
            "roundId": round_id,
            "capacities": capacities,
        }
    )


@app.post("/api/submit")
def submit_answer():
    payload = request.get_json(silent=True) or {}
    round_id = payload.get("roundId")
    answer = payload.get("answer")
    player_name = (payload.get("playerName") or "").strip()

    if not round_id or answer is None:
        return jsonify({"error": "roundId and answer are required"}), 400

    try:
        answer = int(answer)
        round_id = int(round_id)
    except ValueError:
        return jsonify({"error": "roundId and answer must be integers"}), 400

    round_row = get_round(DB_PATH, round_id)
    if not round_row:
        return jsonify({"error": "Round not found"}), 404

    correct = int(round_row["correct_max_flow"])
    diff = abs(answer - correct)

    if diff == 0:
        result = "win"
        if player_name:
            save_win(DB_PATH, player_name, answer, round_id)
    elif diff <= DRAW_MARGIN:
        result = "draw"
    else:
        result = "lose"

    return jsonify(
        {
            "result": result,
            "correctMaxFlow": correct,
            "fordFulkersonMs": round(round_row["ff_time_ms"], 4),
            "edmondsKarpMs": round(round_row["ek_time_ms"], 4),
        }
    )


@app.get("/api/leaderboard")
def leaderboard():
    rows = get_leaderboard(DB_PATH)
    return jsonify(
        [
            {
                "playerName": row["player_name"],
                "wins": row["wins"],
            }
            for row in rows
        ]
    )


def create_app(db_path: Path = DB_PATH):
    global DB_PATH
    DB_PATH = Path(db_path)
    init_db(DB_PATH)
    return app


if __name__ == "__main__":
    init_db(DB_PATH)
    app.run(debug=True)

