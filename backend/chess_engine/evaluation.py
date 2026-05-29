"""
Position evaluation for the chess engine.

Features:
  - Material counting with standard piece values
  - Piece-square tables (separate middlegame and endgame)
  - Tapered evaluation (smooth transition between game phases)
  - Mobility bonus
  - King safety (pawn shield)
  - Passed pawn bonus
  - Bishop pair bonus
"""

from .board import WHITE_PIECES, BLACK_PIECES
from .moves import generate_legal_moves, is_in_check

# ── Material values (centipawns) ──────────────────────────────────────────────

MATERIAL = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000,
            'p': 100, 'n': 320, 'b': 330, 'r': 500, 'q': 900, 'k': 20000}

# Phase weights for tapered eval (total = 24 at start)
PHASE_WEIGHT = {'N': 1, 'B': 1, 'R': 2, 'Q': 4,
                'n': 1, 'b': 1, 'r': 2, 'q': 4}
TOTAL_PHASE = 24

# ── Piece-Square Tables ───────────────────────────────────────────────────────
# Values from white's perspective (row 0 = rank 8, row 7 = rank 1)
# Black tables are mirrored vertically.

# fmt: off
PAWN_MG = [
    [  0,   0,   0,   0,   0,   0,   0,   0],
    [ 50,  50,  50,  50,  50,  50,  50,  50],
    [ 10,  10,  20,  30,  30,  20,  10,  10],
    [  5,   5,  10,  25,  25,  10,   5,   5],
    [  0,   0,   0,  20,  20,   0,   0,   0],
    [  5,  -5, -10,   0,   0, -10,  -5,   5],
    [  5,  10,  10, -20, -20,  10,  10,   5],
    [  0,   0,   0,   0,   0,   0,   0,   0],
]

PAWN_EG = [
    [  0,   0,   0,   0,   0,   0,   0,   0],
    [ 80,  80,  80,  80,  80,  80,  80,  80],
    [ 50,  50,  50,  50,  50,  50,  50,  50],
    [ 30,  30,  30,  30,  30,  30,  30,  30],
    [ 20,  20,  20,  20,  20,  20,  20,  20],
    [ 10,  10,  10,  10,  10,  10,  10,  10],
    [ 10,  10,  10,  10,  10,  10,  10,  10],
    [  0,   0,   0,   0,   0,   0,   0,   0],
]

KNIGHT_MG = [
    [-50, -40, -30, -30, -30, -30, -40, -50],
    [-40, -20,   0,   0,   0,   0, -20, -40],
    [-30,   0,  10,  15,  15,  10,   0, -30],
    [-30,   5,  15,  20,  20,  15,   5, -30],
    [-30,   0,  15,  20,  20,  15,   0, -30],
    [-30,   5,  10,  15,  15,  10,   5, -30],
    [-40, -20,   0,   5,   5,   0, -20, -40],
    [-50, -40, -30, -30, -30, -30, -40, -50],
]

KNIGHT_EG = [
    [-50, -40, -30, -30, -30, -30, -40, -50],
    [-40, -20,   0,   0,   0,   0, -20, -40],
    [-30,   0,  10,  15,  15,  10,   0, -30],
    [-30,   5,  15,  20,  20,  15,   5, -30],
    [-30,   0,  15,  20,  20,  15,   0, -30],
    [-30,   5,  10,  15,  15,  10,   5, -30],
    [-40, -20,   0,   5,   5,   0, -20, -40],
    [-50, -40, -30, -30, -30, -30, -40, -50],
]

BISHOP_MG = [
    [-20, -10, -10, -10, -10, -10, -10, -20],
    [-10,   0,   0,   0,   0,   0,   0, -10],
    [-10,   0,   5,  10,  10,   5,   0, -10],
    [-10,   5,   5,  10,  10,   5,   5, -10],
    [-10,   0,  10,  10,  10,  10,   0, -10],
    [-10,  10,  10,  10,  10,  10,  10, -10],
    [-10,   5,   0,   0,   0,   0,   5, -10],
    [-20, -10, -10, -10, -10, -10, -10, -20],
]

BISHOP_EG = [
    [-20, -10, -10, -10, -10, -10, -10, -20],
    [-10,   0,   0,   0,   0,   0,   0, -10],
    [-10,   0,   5,  10,  10,   5,   0, -10],
    [-10,   5,   5,  10,  10,   5,   5, -10],
    [-10,   0,  10,  10,  10,  10,   0, -10],
    [-10,  10,  10,  10,  10,  10,  10, -10],
    [-10,   5,   0,   0,   0,   0,   5, -10],
    [-20, -10, -10, -10, -10, -10, -10, -20],
]

ROOK_MG = [
    [  0,   0,   0,   0,   0,   0,   0,   0],
    [  5,  10,  10,  10,  10,  10,  10,   5],
    [ -5,   0,   0,   0,   0,   0,   0,  -5],
    [ -5,   0,   0,   0,   0,   0,   0,  -5],
    [ -5,   0,   0,   0,   0,   0,   0,  -5],
    [ -5,   0,   0,   0,   0,   0,   0,  -5],
    [ -5,   0,   0,   0,   0,   0,   0,  -5],
    [  0,   0,   0,   5,   5,   0,   0,   0],
]

ROOK_EG = [
    [  0,   0,   0,   0,   0,   0,   0,   0],
    [  5,  10,  10,  10,  10,  10,  10,   5],
    [ -5,   0,   0,   0,   0,   0,   0,  -5],
    [ -5,   0,   0,   0,   0,   0,   0,  -5],
    [ -5,   0,   0,   0,   0,   0,   0,  -5],
    [ -5,   0,   0,   0,   0,   0,   0,  -5],
    [ -5,   0,   0,   0,   0,   0,   0,  -5],
    [  0,   0,   0,   5,   5,   0,   0,   0],
]

QUEEN_MG = [
    [-20, -10, -10,  -5,  -5, -10, -10, -20],
    [-10,   0,   0,   0,   0,   0,   0, -10],
    [-10,   0,   5,   5,   5,   5,   0, -10],
    [ -5,   0,   5,   5,   5,   5,   0,  -5],
    [  0,   0,   5,   5,   5,   5,   0,  -5],
    [-10,   5,   5,   5,   5,   5,   0, -10],
    [-10,   0,   5,   0,   0,   0,   0, -10],
    [-20, -10, -10,  -5,  -5, -10, -10, -20],
]

QUEEN_EG = [
    [-20, -10, -10,  -5,  -5, -10, -10, -20],
    [-10,   0,   0,   0,   0,   0,   0, -10],
    [-10,   0,   5,   5,   5,   5,   0, -10],
    [ -5,   0,   5,  10,  10,   5,   0,  -5],
    [ -5,   0,   5,  10,  10,   5,   0,  -5],
    [-10,   0,   5,   5,   5,   5,   0, -10],
    [-10,   0,   0,   0,   0,   0,   0, -10],
    [-20, -10, -10,  -5,  -5, -10, -10, -20],
]

KING_MG = [
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-20, -30, -30, -40, -40, -30, -30, -20],
    [-10, -20, -20, -20, -20, -20, -20, -10],
    [ 20,  20,   0,   0,   0,   0,  20,  20],
    [ 20,  30,  10,   0,   0,  10,  30,  20],
]

KING_EG = [
    [-50, -40, -30, -20, -20, -30, -40, -50],
    [-30, -20, -10,   0,   0, -10, -20, -30],
    [-30, -10,  20,  30,  30,  20, -10, -30],
    [-30, -10,  30,  40,  40,  30, -10, -30],
    [-30, -10,  30,  40,  40,  30, -10, -30],
    [-30, -10,  20,  30,  30,  20, -10, -30],
    [-30, -30,   0,   0,   0,   0, -30, -30],
    [-50, -30, -30, -30, -30, -30, -30, -50],
]
# fmt: on

# Lookup tables indexed by piece character
PST_MG = {
    'P': PAWN_MG, 'N': KNIGHT_MG, 'B': BISHOP_MG,
    'R': ROOK_MG, 'Q': QUEEN_MG, 'K': KING_MG,
}
PST_EG = {
    'P': PAWN_EG, 'N': KNIGHT_EG, 'B': BISHOP_EG,
    'R': ROOK_EG, 'Q': QUEEN_EG, 'K': KING_EG,
}


# ── Evaluation function ──────────────────────────────────────────────────────

def evaluate(board):
    """
    Evaluate the current position.

    Returns a score in centipawns from the perspective of the side to move.
    Positive = good for the side to move.
    """
    score = _evaluate_absolute(board)
    return score if board.white_to_move else -score


def _evaluate_absolute(board):
    """
    Evaluate from white's perspective (positive = white is better).
    Uses tapered evaluation to blend middlegame and endgame scores.
    """
    mg_score = 0
    eg_score = 0
    phase = 0
    white_bishops = 0
    black_bishops = 0

    for r in range(8):
        for c in range(8):
            piece = board.squares[r][c]
            if piece == '.':
                continue

            pt = piece.upper()
            is_white = piece in WHITE_PIECES

            # Material
            mat = MATERIAL[piece]

            # Piece-square table value
            if is_white:
                pst_mg = PST_MG[pt][r][c]
                pst_eg = PST_EG[pt][r][c]
            else:
                # Mirror vertically for black
                pst_mg = PST_MG[pt][7 - r][c]
                pst_eg = PST_EG[pt][7 - r][c]

            total_mg = mat + pst_mg
            total_eg = mat + pst_eg

            if is_white:
                mg_score += total_mg
                eg_score += total_eg
                if pt == 'B':
                    white_bishops += 1
            else:
                mg_score -= total_mg
                eg_score -= total_eg
                if pt == 'B':
                    black_bishops += 1

            # Accumulate phase (non-pawn, non-king)
            if piece in PHASE_WEIGHT:
                phase += PHASE_WEIGHT[piece]

    # Bishop pair bonus
    if white_bishops >= 2:
        mg_score += 30
        eg_score += 50
    if black_bishops >= 2:
        mg_score -= 30
        eg_score -= 50

    # Passed pawn bonus
    mg_score += _passed_pawn_bonus(board, True)
    mg_score -= _passed_pawn_bonus(board, False)

    # King safety (middlegame only)
    mg_score += _king_safety(board, True)
    mg_score -= _king_safety(board, False)

    # Tapered evaluation: blend MG and EG scores based on game phase
    phase = min(phase, TOTAL_PHASE)
    mg_weight = phase
    eg_weight = TOTAL_PHASE - phase

    score = (mg_score * mg_weight + eg_score * eg_weight) // TOTAL_PHASE

    return score


def _passed_pawn_bonus(board, white):
    """Calculate bonus for passed pawns (no opposing pawns can block/capture)."""
    bonus = 0
    pawn = 'P' if white else 'p'
    opp_pawn = 'p' if white else 'P'
    direction = -1 if white else 1

    for r in range(8):
        for c in range(8):
            if board.squares[r][c] != pawn:
                continue

            is_passed = True
            # Check files c-1, c, c+1 for opponent pawns ahead
            for fc in range(max(0, c - 1), min(8, c + 2)):
                if white:
                    check_range = range(0, r)
                else:
                    check_range = range(r + 1, 8)
                for fr in check_range:
                    if board.squares[fr][fc] == opp_pawn:
                        is_passed = False
                        break
                if not is_passed:
                    break

            if is_passed:
                # Bonus increases as pawn advances
                if white:
                    rank_bonus = (7 - r) * 10
                else:
                    rank_bonus = r * 10
                bonus += rank_bonus

    return bonus


def _king_safety(board, white):
    """Evaluate king safety based on pawn shield."""
    king_pos = board.find_king(white)
    if king_pos is None:
        return 0

    kr, kc = king_pos
    pawn = 'P' if white else 'p'
    bonus = 0

    # Check for pawn shield in front of king
    shield_row = kr - 1 if white else kr + 1

    if 0 <= shield_row < 8:
        for dc in range(-1, 2):
            sc = kc + dc
            if 0 <= sc < 8 and board.squares[shield_row][sc] == pawn:
                bonus += 10

    return bonus


# ── Checkmate / stalemate scoring ─────────────────────────────────────────────

CHECKMATE_SCORE = 100000
STALEMATE_SCORE = 0


def is_checkmate(board):
    """Check if the current side is in checkmate."""
    if not is_in_check(board, board.white_to_move):
        return False
    return len(generate_legal_moves(board)) == 0


def is_stalemate(board):
    """Check if the current side is in stalemate."""
    if is_in_check(board, board.white_to_move):
        return False
    return len(generate_legal_moves(board)) == 0


def is_draw(board):
    """Check for draw conditions (stalemate, 50-move rule, threefold repetition, insufficient material)."""
    if is_stalemate(board):
        return True
    if board.half_move_clock >= 100:  # 50-move rule
        return True
    if board.is_threefold_repetition():
        return True
    if _insufficient_material(board):
        return True
    return False


def _insufficient_material(board):
    """Check for insufficient material to checkmate."""
    white_pieces = []
    black_pieces = []

    for r in range(8):
        for c in range(8):
            p = board.squares[r][c]
            if p in WHITE_PIECES and p != 'K':
                white_pieces.append(p)
            elif p in BLACK_PIECES and p != 'k':
                black_pieces.append(p)

    # K vs K
    if not white_pieces and not black_pieces:
        return True

    # K+minor vs K
    if not white_pieces and len(black_pieces) == 1 and black_pieces[0] in ('n', 'b'):
        return True
    if not black_pieces and len(white_pieces) == 1 and white_pieces[0] in ('N', 'B'):
        return True

    # K+B vs K+B (same color bishops)
    if (len(white_pieces) == 1 and white_pieces[0] == 'B' and
            len(black_pieces) == 1 and black_pieces[0] == 'b'):
        return True

    return False
