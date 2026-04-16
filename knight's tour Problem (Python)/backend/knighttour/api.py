"""REST API server for Knight's Tour solver."""

from datetime import datetime
from typing import Any

from flask import Flask, jsonify, request
from flask_cors import CORS

from .algorithms import Position, solve_backtracking, solve_warnsdorff, validate_path
from .storage import get_round_scores, get_winners, save_round_score, save_winner

app = Flask(__name__)
CORS(app, origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:5175", "http://localhost:5176"])


def _normalize_path(path: Any) -> list[tuple[int, int]]:
    if not isinstance(path, list):
        return []

    normalized: list[tuple[int, int]] = []
    for step in path:
        if not isinstance(step, (list, tuple)) or len(step) < 2:
            continue
        try:
            row = int(step[0])
            col = int(step[1])
        except (TypeError, ValueError):
            continue
        normalized.append((row, col))
    return normalized


def _format_square(row: int, col: int) -> str:
    # UI is 1-indexed for players.
    return f"({row + 1}, {col + 1})"


@app.route("/api/solve", methods=["POST"])
def solve():
    """Solve knight tour with specified parameters."""
    data = request.get_json()
    
    size = data.get("size", 8)
    solver = data.get("solver", "warnsdorff")
    start_row = data.get("startRow", 0)
    start_col = data.get("startCol", 0)
    node_limit = data.get("nodeLimit", 3_500_000)
    
    # Validate inputs
    if size not in [4, 6, 8, 16]:
        return jsonify({"error": "Invalid board size"}), 400
    if solver not in ["warnsdorff", "backtracking"]:
        return jsonify({"error": "Invalid solver"}), 400
    
    try:
        start = Position(start_row, start_col)
        
        if solver == "warnsdorff":
            path = solve_warnsdorff(size, start)
        else:
            path = solve_backtracking(size, start, node_limit)
        
        if path is None:
            return jsonify({"valid": False, "reason": "No complete tour found", "coverage": 0}), 200
        
        report = validate_path(size, path, start)
        
        return jsonify({
            "valid": report.valid,
            "reason": report.reason,
            "coverage": report.coverage,
            "moves": len(path),
            "path": [(p.row, p.col) for p in path],
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/winners", methods=["GET"])
def get_all_winners():
    """Get all saved winners."""
    try:
        winners = get_winners()
        return jsonify({"winners": winners}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/winners", methods=["POST"])
def add_winner():
    """Save a new winner."""
    data = request.get_json(silent=True) or {}

    path = _normalize_path(data.get("path", []))
    sequence = [_format_square(row, col) for row, col in path]
    start = sequence[0] if sequence else str(data.get("start", "(1, 1)"))

    try:
        size = int(data.get("size", 8))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid board size"}), 400

    path_length_raw = data.get("pathLength", data.get("moves", len(path)))
    try:
        path_length = int(path_length_raw)
    except (TypeError, ValueError):
        path_length = len(path)

    winner = {
        "player": data.get("player", "Anonymous"),
        "size": size,
        "start": start,
        "pathLength": path_length,
        "sequence": sequence,
        "timestamp": datetime.now().isoformat(),
    }
    
    try:
        save_winner(winner)
        return jsonify({"success": True, "winner": winner}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/scores", methods=["GET"])
def get_scores():
    """Get recent round scores for all outcomes."""
    try:
        scores = get_round_scores()
        return jsonify({"scores": scores}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/scores", methods=["POST"])
def add_score():
    """Save round score (win/lose/draw) for a player."""
    data = request.get_json(silent=True) or {}

    try:
        size = int(data.get("size", 8))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid board size"}), 400

    try:
        score = int(data.get("score", 0))
    except (TypeError, ValueError):
        score = 0

    result = str(data.get("result", "draw")).lower()
    if result not in {"win", "lose", "draw"}:
        result = "draw"

    payload = {
        "player": str(data.get("player", "Player")).strip() or "Player",
        "size": size,
        "start": str(data.get("start", "(1, 1)")),
        "score": score,
        "result": result,
        "timestamp": datetime.now().isoformat(),
    }

    try:
        save_round_score(payload)
        return jsonify({"success": True, "score": payload}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)


def run_server():
    """Entry point for CLI"""
    app.run(debug=True, host="0.0.0.0", port=5000)
