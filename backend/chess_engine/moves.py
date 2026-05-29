"""
Legal move generation for all chess pieces.

Generates pseudo-legal moves first, then filters out
moves that leave the king in check.

Includes move ordering for Alpha-Beta efficiency:
  1. Captures ordered by MVV-LVA (Most Valuable Victim - Least Valuable Attacker)
  2. Killer moves (moves that caused beta cutoffs in sibling nodes)
  3. History heuristic (moves that frequently cause cutoffs)
"""

from .board import Move, WHITE_PIECES, BLACK_PIECES

# ── Constants ──────────────────────────────────────────────────────────────────

# Direction vectors for sliding pieces
BISHOP_DIRS = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
ROOK_DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1)]
QUEEN_DIRS = BISHOP_DIRS + ROOK_DIRS
KNIGHT_OFFSETS = [(-2, -1), (-2, 1), (-1, -2), (-1, 2),
                  (1, -2), (1, 2), (2, -1), (2, 1)]
KING_OFFSETS = [(-1, -1), (-1, 0), (-1, 1), (0, -1),
                (0, 1), (1, -1), (1, 0), (1, 1)]

# Material values for MVV-LVA ordering
PIECE_VALUES = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 100,
                'p': 1, 'n': 3, 'b': 3, 'r': 5, 'q': 9, 'k': 100}

PROMOTION_PIECES_WHITE = ['Q', 'R', 'B', 'N']
PROMOTION_PIECES_BLACK = ['q', 'r', 'b', 'n']


# ── Move generation ───────────────────────────────────────────────────────────

def in_bounds(r, c):
    """Check if (r, c) is within the 8x8 board."""
    return 0 <= r < 8 and 0 <= c < 8


def is_square_attacked(board, row, col, by_white):
    """
    Check if a square is attacked by pieces of the given color.
    Used for check detection and castling legality.
    """
    # Check for pawn attacks
    if by_white:
        # White pawns attack diagonally upward (decreasing row)
        for dc in [-1, 1]:
            pr, pc = row + 1, col + dc
            if in_bounds(pr, pc) and board.squares[pr][pc] == 'P':
                return True
    else:
        # Black pawns attack diagonally downward (increasing row)
        for dc in [-1, 1]:
            pr, pc = row - 1, col + dc
            if in_bounds(pr, pc) and board.squares[pr][pc] == 'p':
                return True

    # Check for knight attacks
    knight = 'N' if by_white else 'n'
    for dr, dc in KNIGHT_OFFSETS:
        nr, nc = row + dr, col + dc
        if in_bounds(nr, nc) and board.squares[nr][nc] == knight:
            return True

    # Check for king attacks
    king = 'K' if by_white else 'k'
    for dr, dc in KING_OFFSETS:
        kr, kc = row + dr, col + dc
        if in_bounds(kr, kc) and board.squares[kr][kc] == king:
            return True

    # Check for sliding piece attacks (bishop/queen diagonals, rook/queen straights)
    bishop = 'B' if by_white else 'b'
    queen = 'Q' if by_white else 'q'
    for dr, dc in BISHOP_DIRS:
        r, c = row + dr, col + dc
        while in_bounds(r, c):
            p = board.squares[r][c]
            if p != '.':
                if p == bishop or p == queen:
                    return True
                break
            r += dr
            c += dc

    rook = 'R' if by_white else 'r'
    for dr, dc in ROOK_DIRS:
        r, c = row + dr, col + dc
        while in_bounds(r, c):
            p = board.squares[r][c]
            if p != '.':
                if p == rook or p == queen:
                    return True
                break
            r += dr
            c += dc

    return False


def is_in_check(board, white):
    """Check if the given side's king is in check."""
    king_pos = board.find_king(white)
    if king_pos is None:
        return True  # King captured (shouldn't happen in legal play)
    return is_square_attacked(board, king_pos[0], king_pos[1], not white)


def generate_pseudo_legal_moves(board):
    """Generate all pseudo-legal moves (may leave king in check)."""
    moves = []
    white = board.white_to_move
    friendly = WHITE_PIECES if white else BLACK_PIECES
    enemy = BLACK_PIECES if white else WHITE_PIECES

    for r in range(8):
        for c in range(8):
            piece = board.squares[r][c]
            if piece not in friendly:
                continue

            pt = piece.upper()

            if pt == 'P':
                _generate_pawn_moves(board, r, c, piece, white, enemy, moves)
            elif pt == 'N':
                _generate_knight_moves(board, r, c, piece, enemy, moves)
            elif pt == 'B':
                _generate_sliding_moves(board, r, c, piece, BISHOP_DIRS, enemy, moves)
            elif pt == 'R':
                _generate_sliding_moves(board, r, c, piece, ROOK_DIRS, enemy, moves)
            elif pt == 'Q':
                _generate_sliding_moves(board, r, c, piece, QUEEN_DIRS, enemy, moves)
            elif pt == 'K':
                _generate_king_moves(board, r, c, piece, white, enemy, moves)

    return moves


def _generate_pawn_moves(board, r, c, piece, white, enemy, moves):
    """Generate pawn moves: single push, double push, captures, en passant, promotion."""
    direction = -1 if white else 1
    start_row = 6 if white else 1
    promo_row = 0 if white else 7
    promo_pieces = PROMOTION_PIECES_WHITE if white else PROMOTION_PIECES_BLACK

    # Single push
    nr = r + direction
    if in_bounds(nr, c) and board.squares[nr][c] == '.':
        if nr == promo_row:
            for pp in promo_pieces:
                moves.append(Move(r, c, nr, c, piece, promotion=pp))
        else:
            moves.append(Move(r, c, nr, c, piece))

            # Double push from starting position
            if r == start_row:
                nnr = r + 2 * direction
                if board.squares[nnr][c] == '.':
                    moves.append(Move(r, c, nnr, c, piece, is_double_pawn_push=True))

    # Captures
    for dc in [-1, 1]:
        nc = c + dc
        if not in_bounds(nr, nc):
            continue

        target = board.squares[nr][nc]
        if target in enemy:
            if nr == promo_row:
                for pp in promo_pieces:
                    moves.append(Move(r, c, nr, nc, piece, captured=target, promotion=pp))
            else:
                moves.append(Move(r, c, nr, nc, piece, captured=target))

        # En passant
        if board.en_passant and (nr, nc) == board.en_passant:
            ep_captured = 'p' if white else 'P'
            moves.append(Move(r, c, nr, nc, piece, captured=ep_captured, is_en_passant=True))


def _generate_knight_moves(board, r, c, piece, enemy, moves):
    """Generate knight moves."""
    for dr, dc in KNIGHT_OFFSETS:
        nr, nc = r + dr, c + dc
        if not in_bounds(nr, nc):
            continue
        target = board.squares[nr][nc]
        if target == '.':
            moves.append(Move(r, c, nr, nc, piece))
        elif target in enemy:
            moves.append(Move(r, c, nr, nc, piece, captured=target))


def _generate_sliding_moves(board, r, c, piece, directions, enemy, moves):
    """Generate sliding piece moves (bishop, rook, queen)."""
    for dr, dc in directions:
        nr, nc = r + dr, c + dc
        while in_bounds(nr, nc):
            target = board.squares[nr][nc]
            if target == '.':
                moves.append(Move(r, c, nr, nc, piece))
            elif target in enemy:
                moves.append(Move(r, c, nr, nc, piece, captured=target))
                break
            else:
                break  # Friendly piece blocks
            nr += dr
            nc += dc


def _generate_king_moves(board, r, c, piece, white, enemy, moves):
    """Generate king moves including castling."""
    for dr, dc in KING_OFFSETS:
        nr, nc = r + dr, c + dc
        if not in_bounds(nr, nc):
            continue
        target = board.squares[nr][nc]
        if target == '.':
            moves.append(Move(r, c, nr, nc, piece))
        elif target in enemy:
            moves.append(Move(r, c, nr, nc, piece, captured=target))

    # Castling
    if white:
        if board.castling_rights['K']:
            _try_castle(board, r, c, piece, white, 7, 4, 6, 7, moves)  # Kingside
        if board.castling_rights['Q']:
            _try_castle(board, r, c, piece, white, 7, 4, 2, 0, moves)  # Queenside
    else:
        if board.castling_rights['k']:
            _try_castle(board, r, c, piece, white, 0, 4, 6, 7, moves)  # Kingside
        if board.castling_rights['q']:
            _try_castle(board, r, c, piece, white, 0, 4, 2, 0, moves)  # Queenside


def _try_castle(board, r, c, piece, white, row, king_col, king_dest, rook_col, moves):
    """Check if castling is legal and add the move."""
    if r != row or c != king_col:
        return

    # Determine direction and squares that must be empty
    if king_dest > king_col:  # Kingside
        empty_range = range(king_col + 1, 7)  # f, g
        check_range = range(king_col, king_col + 3)  # e, f, g
    else:  # Queenside
        empty_range = range(1, king_col)  # b, c, d
        check_range = range(king_dest, king_col + 1)  # c, d, e

    # All squares between king and rook must be empty
    for cc in empty_range:
        if board.squares[row][cc] != '.':
            return

    # King must not pass through or end on an attacked square
    attacker = not white
    for cc in check_range:
        if is_square_attacked(board, row, cc, attacker):
            return

    moves.append(Move(r, c, row, king_dest, piece, is_castling=True))


def generate_legal_moves(board):
    """
    Generate all legal moves for the current position.
    Filters pseudo-legal moves by rejecting those that leave the king in check.
    """
    pseudo_moves = generate_pseudo_legal_moves(board)
    legal_moves = []

    for move in pseudo_moves:
        board.make_move(move)
        # After making the move, it's the opponent's turn,
        # so we check if our king is in check
        if not is_in_check(board, not board.white_to_move):
            legal_moves.append(move)
        board.undo_move()

    return legal_moves


def get_legal_moves_for_square(board, row, col):
    """Get legal moves originating from a specific square."""
    all_moves = generate_legal_moves(board)
    return [m for m in all_moves if m.from_row == row and m.from_col == col]


# ── Move ordering ─────────────────────────────────────────────────────────────

class MoveOrderer:
    """
    Orders moves for optimal Alpha-Beta pruning efficiency.

    Priority:
      1. Hash move (from transposition table)
      2. Captures (MVV-LVA ordering)
      3. Killer moves (caused beta cutoffs at same ply)
      4. History heuristic (moves that frequently cause cutoffs)
      5. Quiet moves
    """

    def __init__(self):
        self.killer_moves = [[None, None] for _ in range(64)]  # 2 killers per ply
        self.history = {}  # (piece, to_row, to_col) -> score

    def order_moves(self, moves, board, ply=0, hash_move=None):
        """Sort moves by estimated quality (best first)."""
        scored = []
        for move in moves:
            score = 0

            # Hash move gets highest priority
            if hash_move and move == hash_move:
                score = 10000000
            elif move.captured != '.':
                # MVV-LVA: capture more valuable piece with less valuable attacker
                victim_val = PIECE_VALUES.get(move.captured, 0)
                attacker_val = PIECE_VALUES.get(move.piece, 0)
                score = 1000000 + victim_val * 100 - attacker_val
            elif move.promotion:
                score = 900000 + PIECE_VALUES.get(move.promotion, 0) * 100
            else:
                # Killer moves
                if ply < 64:
                    if move == self.killer_moves[ply][0]:
                        score = 800000
                    elif move == self.killer_moves[ply][1]:
                        score = 700000

                # History heuristic
                key = (move.piece, move.to_row, move.to_col)
                score += self.history.get(key, 0)

            scored.append((score, move))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [m for _, m in scored]

    def update_killer(self, move, ply):
        """Record a killer move (caused beta cutoff)."""
        if ply >= 64:
            return
        if move.captured == '.' and move != self.killer_moves[ply][0]:
            self.killer_moves[ply][1] = self.killer_moves[ply][0]
            self.killer_moves[ply][0] = move

    def update_history(self, move, depth):
        """Update history heuristic for a move that caused a cutoff."""
        if move.captured != '.':
            return
        key = (move.piece, move.to_row, move.to_col)
        self.history[key] = self.history.get(key, 0) + depth * depth

    def clear(self):
        """Reset move ordering heuristics."""
        self.killer_moves = [[None, None] for _ in range(64)]
        self.history = {}
