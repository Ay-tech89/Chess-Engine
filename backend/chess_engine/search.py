"""
AI Search engine using Negamax with Alpha-Beta Pruning.

Features:
  - Negamax (simplified Minimax from one side's perspective)
  - Alpha-Beta pruning with fail-soft
  - Iterative deepening
  - Quiescence search (extends search for captures)
  - Transposition table with Zobrist hashing
  - Move ordering (MVV-LVA, killer moves, history heuristic)
"""

import time
from .moves import generate_legal_moves, is_in_check, MoveOrderer
from .evaluation import evaluate, CHECKMATE_SCORE, is_draw

# ── Transposition Table ───────────────────────────────────────────────────────

# Entry types
TT_EXACT = 0
TT_ALPHA = 1  # Upper bound (failed low)
TT_BETA = 2   # Lower bound (failed high)

# Maximum TT size (entries)
TT_MAX_SIZE = 1 << 20  # ~1 million entries


class TTEntry:
    """Transposition table entry."""
    __slots__ = ['hash_key', 'depth', 'score', 'flag', 'best_move']

    def __init__(self, hash_key, depth, score, flag, best_move=None):
        self.hash_key = hash_key
        self.depth = depth
        self.score = score
        self.flag = flag
        self.best_move = best_move


class TranspositionTable:
    """Hash table mapping positions (Zobrist hash) to search results."""

    def __init__(self, size=TT_MAX_SIZE):
        self.size = size
        self.table = {}

    def store(self, hash_key, depth, score, flag, best_move=None):
        """Store a position in the table (always-replace scheme)."""
        idx = hash_key % self.size
        existing = self.table.get(idx)
        # Replace if new search is deeper or same position
        if existing is None or existing.hash_key == hash_key or depth >= existing.depth:
            self.table[idx] = TTEntry(hash_key, depth, score, flag, best_move)

    def probe(self, hash_key):
        """Look up a position. Returns TTEntry or None."""
        idx = hash_key % self.size
        entry = self.table.get(idx)
        if entry and entry.hash_key == hash_key:
            return entry
        return None

    def clear(self):
        """Clear the transposition table."""
        self.table.clear()


# ── Search engine ─────────────────────────────────────────────────────────────

class SearchEngine:
    """
    Chess AI using Negamax with Alpha-Beta pruning.

    Adjustable difficulty via search depth:
      Easy   = depth 2
      Medium = depth 3
      Hard   = depth 4
      Expert = depth 5
    """

    DIFFICULTY_DEPTHS = {
        'easy': 2,
        'medium': 3,
        'hard': 4,
        'expert': 5,
    }

    def __init__(self):
        self.tt = TranspositionTable()
        self.orderer = MoveOrderer()
        self.nodes_searched = 0
        self.max_depth = 4
        self.best_move = None
        self.search_info = {}
        self.start_time = 0
        self.time_limit = 30  # seconds

    def set_difficulty(self, difficulty):
        """Set AI difficulty level."""
        difficulty = difficulty.lower()
        if difficulty in self.DIFFICULTY_DEPTHS:
            self.max_depth = self.DIFFICULTY_DEPTHS[difficulty]
        else:
            self.max_depth = 4

    def find_best_move(self, board):
        """
        Find the best move using iterative deepening.

        Returns the best Move object found, or None if no legal moves.
        """
        self.nodes_searched = 0
        self.best_move = None
        self.start_time = time.time()
        self.search_info = {}

        legal_moves = generate_legal_moves(board)
        if not legal_moves:
            return None

        if len(legal_moves) == 1:
            self.best_move = legal_moves[0]
            self.search_info = {
                'depth': 0,
                'nodes': 1,
                'time': 0,
                'score': 0,
            }
            return legal_moves[0]

        best_move = legal_moves[0]
        best_score = -CHECKMATE_SCORE

        # Iterative deepening: search depth 1, 2, ..., max_depth
        for depth in range(1, self.max_depth + 1):
            try:
                score = self._negamax_root(board, depth, legal_moves)
                if self.best_move:
                    best_move = self.best_move
                    best_score = score

                elapsed = time.time() - self.start_time
                self.search_info = {
                    'depth': depth,
                    'nodes': self.nodes_searched,
                    'time': round(elapsed, 2),
                    'score': best_score,
                }

                # If checkmate found, stop early
                if abs(best_score) > CHECKMATE_SCORE - 100:
                    break

                # Time check
                if elapsed > self.time_limit * 0.7:
                    break

            except TimeoutError:
                break

        self.best_move = best_move
        return best_move

    def _negamax_root(self, board, depth, legal_moves):
        """Root-level negamax search with Alpha-Beta pruning."""
        alpha = -CHECKMATE_SCORE
        beta = CHECKMATE_SCORE
        best_score = -CHECKMATE_SCORE

        # Get hash move from TT for ordering
        tt_entry = self.tt.probe(board.zobrist_hash)
        hash_move = tt_entry.best_move if tt_entry else None

        ordered_moves = self.orderer.order_moves(legal_moves, board, 0, hash_move)

        for move in ordered_moves:
            board.make_move(move)
            score = -self._negamax(board, depth - 1, -beta, -alpha, 1)
            board.undo_move()

            if score > best_score:
                best_score = score
                self.best_move = move

            if score > alpha:
                alpha = score

        # Store in TT
        self.tt.store(board.zobrist_hash, depth, best_score, TT_EXACT, self.best_move)

        return best_score

    def _negamax(self, board, depth, alpha, beta, ply):
        """
        Negamax with Alpha-Beta pruning.

        Returns score from the perspective of the side to move.
        """
        self.nodes_searched += 1

        # Time check (every 4096 nodes)
        if self.nodes_searched & 4095 == 0:
            if time.time() - self.start_time > self.time_limit:
                raise TimeoutError()

        # Check for draw
        if is_draw(board):
            return 0

        # Transposition table lookup
        alpha_orig = alpha
        tt_entry = self.tt.probe(board.zobrist_hash)
        hash_move = None

        if tt_entry and tt_entry.depth >= depth:
            hash_move = tt_entry.best_move
            if tt_entry.flag == TT_EXACT:
                return tt_entry.score
            elif tt_entry.flag == TT_ALPHA:
                if tt_entry.score <= alpha:
                    return alpha
            elif tt_entry.flag == TT_BETA:
                if tt_entry.score >= beta:
                    return beta
        elif tt_entry:
            hash_move = tt_entry.best_move

        # Leaf node: use quiescence search
        if depth <= 0:
            return self._quiescence(board, alpha, beta, ply)

        legal_moves = generate_legal_moves(board)

        # No legal moves: checkmate or stalemate
        if not legal_moves:
            if is_in_check(board, board.white_to_move):
                return -(CHECKMATE_SCORE - ply)  # Checkmate (prefer shorter mates)
            return 0  # Stalemate

        # Order moves for better pruning
        ordered_moves = self.orderer.order_moves(legal_moves, board, ply, hash_move)

        best_score = -CHECKMATE_SCORE
        best_move = ordered_moves[0]

        for move in ordered_moves:
            board.make_move(move)
            score = -self._negamax(board, depth - 1, -beta, -alpha, ply + 1)
            board.undo_move()

            if score > best_score:
                best_score = score
                best_move = move

            if score > alpha:
                alpha = score

            if alpha >= beta:
                # Beta cutoff — update killer and history
                self.orderer.update_killer(move, ply)
                self.orderer.update_history(move, depth)
                break

        # Store in transposition table
        if best_score <= alpha_orig:
            flag = TT_ALPHA
        elif best_score >= beta:
            flag = TT_BETA
        else:
            flag = TT_EXACT

        self.tt.store(board.zobrist_hash, depth, best_score, flag, best_move)

        return best_score

    def _quiescence(self, board, alpha, beta, ply):
        """
        Quiescence search: extend search for captures to avoid horizon effect.

        Only considers captures and promotions to reach a "quiet" position.
        """
        self.nodes_searched += 1

        stand_pat = evaluate(board)

        if stand_pat >= beta:
            return beta

        if stand_pat > alpha:
            alpha = stand_pat

        # Generate only capture moves
        legal_moves = generate_legal_moves(board)
        captures = [m for m in legal_moves if m.captured != '.' or m.promotion]

        if not captures:
            return alpha

        # Order captures by MVV-LVA
        ordered = self.orderer.order_moves(captures, board, ply)

        for move in ordered:
            board.make_move(move)
            score = -self._quiescence(board, -beta, -alpha, ply + 1)
            board.undo_move()

            if score >= beta:
                return beta

            if score > alpha:
                alpha = score

        return alpha

    def get_search_info(self):
        """Get info about the last search performed."""
        return self.search_info
