"""
Flask API for the Chess Engine.

Provides REST endpoints for the frontend to interact with the chess engine.
All state is managed server-side in a single ChessGame instance.
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from chess_engine import ChessGame

# ── App setup ─────────────────────────────────────────────────────────────────

app = Flask(__name__)
CORS(app)  # Allow frontend cross-origin requests

# Single game instance (for simplicity; could be extended to sessions)
game = ChessGame()


# ── API Routes ────────────────────────────────────────────────────────────────

@app.route('/api/new-game', methods=['POST'])
def new_game():
    """Start a new chess game."""
    data = request.get_json(silent=True) or {}
    difficulty = data.get('difficulty', game.difficulty)
    game.set_difficulty(difficulty)
    game.new_game()
    return jsonify(game.get_state())


@app.route('/api/game-state', methods=['GET'])
def get_game_state():
    """Get the current game state."""
    return jsonify(game.get_state())


@app.route('/api/move', methods=['POST'])
def make_move():
    """
    Make a player move.

    Request body:
        {
            "from": "e2" or {"row": 6, "col": 4},
            "to": "e4" or {"row": 4, "col": 4},
            "promotion": "Q" (optional)
        }
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Missing request body'}), 400

    from_sq = data.get('from')
    to_sq = data.get('to')
    promotion = data.get('promotion')

    if not from_sq or not to_sq:
        return jsonify({'error': 'Missing from/to squares'}), 400

    result = game.make_player_move(from_sq, to_sq, promotion)

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result)


@app.route('/api/ai-move', methods=['POST'])
def ai_move():
    """Trigger the AI to compute and make its move."""
    result = game.make_ai_move()

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result)


@app.route('/api/legal-moves', methods=['GET'])
def get_legal_moves():
    """
    Get legal moves for a piece at the given square.

    Query params:
        square: e.g., 'e2'
        OR
        row & col: e.g., row=6&col=4
    """
    square = request.args.get('square')
    row = request.args.get('row', type=int)
    col = request.args.get('col', type=int)

    if square:
        moves = game.get_legal_moves(square)
    elif row is not None and col is not None:
        moves = game.get_legal_moves((row, col))
    else:
        return jsonify({'error': 'Provide square or row+col'}), 400

    return jsonify({'moves': moves})


@app.route('/api/undo', methods=['POST'])
def undo_move():
    """Undo the last move pair (player + AI)."""
    result = game.undo()
    if 'error' in result:
        return jsonify(result), 400
    return jsonify(result)


@app.route('/api/redo', methods=['POST'])
def redo_move():
    """Redo the last undone move pair."""
    result = game.redo()
    if 'error' in result:
        return jsonify(result), 400
    return jsonify(result)


@app.route('/api/set-difficulty', methods=['POST'])
def set_difficulty():
    """
    Set the AI difficulty level.

    Request body: { "difficulty": "easy" | "medium" | "hard" | "expert" }
    """
    data = request.get_json()
    if not data or 'difficulty' not in data:
        return jsonify({'error': 'Missing difficulty'}), 400

    difficulty = data['difficulty']
    game.set_difficulty(difficulty)
    return jsonify({'difficulty': game.difficulty, 'message': f'Difficulty set to {game.difficulty}'})


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print("♟ Chess Engine API starting...")
    print("  Endpoints:")
    print("    POST /api/new-game")
    print("    GET  /api/game-state")
    print("    POST /api/move")
    print("    POST /api/ai-move")
    print("    GET  /api/legal-moves?square=e2")
    print("    POST /api/undo")
    print("    POST /api/redo")
    print("    POST /api/set-difficulty")
    app.run(debug=True, port=5000)
