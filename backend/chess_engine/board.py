"""
Board representation for the chess engine.

Uses an 8x8 array with piece characters:
  Uppercase = White (P, N, B, R, Q, K)
  Lowercase = Black (p, n, b, r, q, k)
  '.' = empty square

Coordinates: (row, col) where row 0 = rank 8 (black's back rank),
row 7 = rank 1 (white's back rank).
"""

import random
import copy

# ── Piece definitions ──────────────────────────────────────────────────────────

PIECES = 'PNBRQKpnbrqk'
WHITE_PIECES = 'PNBRQK'
BLACK_PIECES = 'pnbrqk'

PIECE_NAMES = {
    'P': 'Pawn', 'N': 'Knight', 'B': 'Bishop', 'R': 'Rook', 'Q': 'Queen', 'K': 'King',
    'p': 'Pawn', 'n': 'Knight', 'b': 'Bishop', 'r': 'Rook', 'q': 'Queen', 'k': 'King',
}

# Unicode symbols for display
PIECE_SYMBOLS = {
    'K': '♔', 'Q': '♕', 'R': '♖', 'B': '♗', 'N': '♘', 'P': '♙',
    'k': '♚', 'q': '♛', 'r': '♜', 'b': '♝', 'n': '♞', 'p': '♟',
    '.': ''
}

# ── Zobrist hashing ────────────────────────────────────────────────────────────

random.seed(42)  # Deterministic for reproducibility

ZOBRIST_PIECES = {}
for piece in PIECES:
    ZOBRIST_PIECES[piece] = [[random.getrandbits(64) for _ in range(8)] for _ in range(8)]

ZOBRIST_BLACK_TO_MOVE = random.getrandbits(64)
ZOBRIST_CASTLING = [random.getrandbits(64) for _ in range(16)]  # 4-bit castling
ZOBRIST_EN_PASSANT = [random.getrandbits(64) for _ in range(8)]  # file 0-7


# ── Move representation ───────────────────────────────────────────────────────

class Move:
    """Represents a chess move."""

    __slots__ = [
        'from_row', 'from_col', 'to_row', 'to_col',
        'piece', 'captured', 'promotion',
        'is_castling', 'is_en_passant', 'is_double_pawn_push',
        'prev_castling_rights', 'prev_en_passant', 'prev_half_move_clock',
        'rook_from', 'rook_to'
    ]

    def __init__(self, from_row, from_col, to_row, to_col, piece,
                 captured='.', promotion=None, is_castling=False,
                 is_en_passant=False, is_double_pawn_push=False):
        self.from_row = from_row
        self.from_col = from_col
        self.to_row = to_row
        self.to_col = to_col
        self.piece = piece
        self.captured = captured
        self.promotion = promotion
        self.is_castling = is_castling
        self.is_en_passant = is_en_passant
        self.is_double_pawn_push = is_double_pawn_push
        # Saved state for undo
        self.prev_castling_rights = None
        self.prev_en_passant = None
        self.prev_half_move_clock = 0
        # Rook move for castling
        self.rook_from = None
        self.rook_to = None

    def to_algebraic(self):
        """Convert to simple algebraic notation like 'e2e4' or 'e7e8q'."""
        files = 'abcdefgh'
        ranks = '87654321'
        s = f"{files[self.from_col]}{ranks[self.from_row]}{files[self.to_col]}{ranks[self.to_row]}"
        if self.promotion:
            s += self.promotion.lower()
        return s

    def to_san(self, board):
        """Convert to Standard Algebraic Notation (e.g., Nf3, O-O, exd5)."""
        if self.is_castling:
            if self.to_col > self.from_col:
                return 'O-O'
            else:
                return 'O-O-O'

        piece = self.piece.upper()
        san = ''

        if piece == 'P':
            # Pawn moves
            files = 'abcdefgh'
            if self.captured != '.' or self.is_en_passant:
                san = files[self.from_col] + 'x'
            ranks = '87654321'
            san += files[self.to_col] + ranks[self.to_row]
            if self.promotion:
                san += '=' + self.promotion.upper()
        else:
            san = piece
            # Disambiguation for knights, rooks, bishops, queens
            files = 'abcdefgh'
            ranks = '87654321'
            if self.captured != '.' or self.is_en_passant:
                san += 'x'
            san += files[self.to_col] + ranks[self.to_row]

        return san

    def __repr__(self):
        return f"Move({self.to_algebraic()})"

    def __eq__(self, other):
        if not isinstance(other, Move):
            return False
        return (self.from_row == other.from_row and self.from_col == other.from_col and
                self.to_row == other.to_row and self.to_col == other.to_col and
                self.promotion == other.promotion)

    def __hash__(self):
        return hash((self.from_row, self.from_col, self.to_row, self.to_col, self.promotion))


# ── Board class ────────────────────────────────────────────────────────────────

class Board:
    """
    Chess board state manager.

    Handles board representation, move making/unmaking, and state tracking.
    """

    INITIAL_FEN = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'

    def __init__(self, fen=None):
        self.squares = [['.' for _ in range(8)] for _ in range(8)]
        self.white_to_move = True
        self.castling_rights = {'K': True, 'Q': True, 'k': True, 'q': True}
        self.en_passant = None  # (row, col) or None
        self.half_move_clock = 0
        self.full_move_number = 1
        self.move_stack = []
        self.zobrist_hash = 0
        self.position_history = {}  # hash -> count for threefold repetition

        if fen:
            self.load_fen(fen)
        else:
            self.load_fen(self.INITIAL_FEN)

        self._compute_zobrist()
        self._record_position()

    def load_fen(self, fen):
        """Load board state from FEN string."""
        parts = fen.split()
        rows = parts[0].split('/')

        for r, row_str in enumerate(rows):
            c = 0
            for ch in row_str:
                if ch.isdigit():
                    for _ in range(int(ch)):
                        self.squares[r][c] = '.'
                        c += 1
                else:
                    self.squares[r][c] = ch
                    c += 1

        self.white_to_move = (parts[1] == 'w')

        castling = parts[2]
        self.castling_rights = {
            'K': 'K' in castling,
            'Q': 'Q' in castling,
            'k': 'k' in castling,
            'q': 'q' in castling,
        }

        if parts[3] != '-':
            file_idx = ord(parts[3][0]) - ord('a')
            rank_idx = 8 - int(parts[3][1])
            self.en_passant = (rank_idx, file_idx)
        else:
            self.en_passant = None

        self.half_move_clock = int(parts[4]) if len(parts) > 4 else 0
        self.full_move_number = int(parts[5]) if len(parts) > 5 else 1

    def to_fen(self):
        """Export board state as FEN string."""
        rows = []
        for r in range(8):
            empty = 0
            row_str = ''
            for c in range(8):
                if self.squares[r][c] == '.':
                    empty += 1
                else:
                    if empty > 0:
                        row_str += str(empty)
                        empty = 0
                    row_str += self.squares[r][c]
            if empty > 0:
                row_str += str(empty)
            rows.append(row_str)

        fen = '/'.join(rows)
        fen += ' w ' if self.white_to_move else ' b '

        castling = ''
        if self.castling_rights['K']: castling += 'K'
        if self.castling_rights['Q']: castling += 'Q'
        if self.castling_rights['k']: castling += 'k'
        if self.castling_rights['q']: castling += 'q'
        fen += castling if castling else '-'

        if self.en_passant:
            files = 'abcdefgh'
            ranks = '87654321'
            fen += f' {files[self.en_passant[1]]}{ranks[self.en_passant[0]]}'
        else:
            fen += ' -'

        fen += f' {self.half_move_clock} {self.full_move_number}'
        return fen

    def _compute_zobrist(self):
        """Compute the full Zobrist hash from scratch."""
        h = 0
        for r in range(8):
            for c in range(8):
                piece = self.squares[r][c]
                if piece != '.':
                    h ^= ZOBRIST_PIECES[piece][r][c]

        if not self.white_to_move:
            h ^= ZOBRIST_BLACK_TO_MOVE

        castling_idx = (
            (self.castling_rights['K'] << 3) |
            (self.castling_rights['Q'] << 2) |
            (self.castling_rights['k'] << 1) |
            (self.castling_rights['q'])
        )
        h ^= ZOBRIST_CASTLING[castling_idx]

        if self.en_passant:
            h ^= ZOBRIST_EN_PASSANT[self.en_passant[1]]

        self.zobrist_hash = h

    def _update_zobrist_piece(self, piece, row, col):
        """Toggle a piece in/out of the Zobrist hash."""
        self.zobrist_hash ^= ZOBRIST_PIECES[piece][row][col]

    def _record_position(self):
        """Record current position for threefold repetition detection."""
        h = self.zobrist_hash
        self.position_history[h] = self.position_history.get(h, 0) + 1

    def _unrecord_position(self):
        """Remove current position from history."""
        h = self.zobrist_hash
        if h in self.position_history:
            self.position_history[h] -= 1
            if self.position_history[h] <= 0:
                del self.position_history[h]

    def is_threefold_repetition(self):
        """Check if current position has occurred 3+ times."""
        return self.position_history.get(self.zobrist_hash, 0) >= 3

    def piece_at(self, row, col):
        """Get the piece at (row, col)."""
        return self.squares[row][col]

    def is_white_piece(self, piece):
        """Check if a piece is white."""
        return piece in WHITE_PIECES

    def is_black_piece(self, piece):
        """Check if a piece is black."""
        return piece in BLACK_PIECES

    def is_friendly(self, piece):
        """Check if a piece belongs to the side to move."""
        if self.white_to_move:
            return piece in WHITE_PIECES
        return piece in BLACK_PIECES

    def is_enemy(self, piece):
        """Check if a piece belongs to the opponent."""
        if self.white_to_move:
            return piece in BLACK_PIECES
        return piece in WHITE_PIECES

    def find_king(self, white):
        """Find the king's position."""
        king = 'K' if white else 'k'
        for r in range(8):
            for c in range(8):
                if self.squares[r][c] == king:
                    return (r, c)
        return None

    def make_move(self, move):
        """
        Apply a move to the board. Saves state for undo.
        """
        # Save state for undo
        move.prev_castling_rights = dict(self.castling_rights)
        move.prev_en_passant = self.en_passant
        move.prev_half_move_clock = self.half_move_clock

        fr, fc = move.from_row, move.from_col
        tr, tc = move.to_row, move.to_col
        piece = move.piece
        captured = move.captured

        # Remove from Zobrist and update hash
        self._unrecord_position()

        # Remove piece from source
        self._update_zobrist_piece(piece, fr, fc)
        self.squares[fr][fc] = '.'

        # Remove captured piece
        if captured != '.':
            if move.is_en_passant:
                # En passant: captured pawn is not on the destination square
                cap_row = fr  # Same row as moving pawn
                self._update_zobrist_piece(captured, cap_row, tc)
                self.squares[cap_row][tc] = '.'
            else:
                self._update_zobrist_piece(captured, tr, tc)

        # Place piece (or promoted piece) on destination
        placed = move.promotion if move.promotion else piece
        self.squares[tr][tc] = placed
        self._update_zobrist_piece(placed, tr, tc)

        # Handle castling rook move
        if move.is_castling:
            if tc > fc:  # Kingside
                rook = 'R' if self.white_to_move else 'r'
                rook_row = fr
                move.rook_from = (rook_row, 7)
                move.rook_to = (rook_row, 5)
                self._update_zobrist_piece(rook, rook_row, 7)
                self.squares[rook_row][7] = '.'
                self.squares[rook_row][5] = rook
                self._update_zobrist_piece(rook, rook_row, 5)
            else:  # Queenside
                rook = 'R' if self.white_to_move else 'r'
                rook_row = fr
                move.rook_from = (rook_row, 0)
                move.rook_to = (rook_row, 3)
                self._update_zobrist_piece(rook, rook_row, 0)
                self.squares[rook_row][0] = '.'
                self.squares[rook_row][3] = rook
                self._update_zobrist_piece(rook, rook_row, 3)

        # Update castling rights
        old_castling = (
            (self.castling_rights['K'] << 3) |
            (self.castling_rights['Q'] << 2) |
            (self.castling_rights['k'] << 1) |
            (self.castling_rights['q'])
        )
        self.zobrist_hash ^= ZOBRIST_CASTLING[old_castling]

        # King moves remove both castling rights
        if piece == 'K':
            self.castling_rights['K'] = False
            self.castling_rights['Q'] = False
        elif piece == 'k':
            self.castling_rights['k'] = False
            self.castling_rights['q'] = False

        # Rook moves or captures remove specific castling rights
        if fr == 7 and fc == 7: self.castling_rights['K'] = False
        if fr == 7 and fc == 0: self.castling_rights['Q'] = False
        if fr == 0 and fc == 7: self.castling_rights['k'] = False
        if fr == 0 and fc == 0: self.castling_rights['q'] = False
        if tr == 7 and tc == 7: self.castling_rights['K'] = False
        if tr == 7 and tc == 0: self.castling_rights['Q'] = False
        if tr == 0 and tc == 7: self.castling_rights['k'] = False
        if tr == 0 and tc == 0: self.castling_rights['q'] = False

        new_castling = (
            (self.castling_rights['K'] << 3) |
            (self.castling_rights['Q'] << 2) |
            (self.castling_rights['k'] << 1) |
            (self.castling_rights['q'])
        )
        self.zobrist_hash ^= ZOBRIST_CASTLING[new_castling]

        # Update en passant
        if self.en_passant:
            self.zobrist_hash ^= ZOBRIST_EN_PASSANT[self.en_passant[1]]

        if move.is_double_pawn_push:
            self.en_passant = ((fr + tr) // 2, fc)
            self.zobrist_hash ^= ZOBRIST_EN_PASSANT[self.en_passant[1]]
        else:
            self.en_passant = None

        # Update clocks
        if piece.upper() == 'P' or captured != '.':
            self.half_move_clock = 0
        else:
            self.half_move_clock += 1

        # Switch side to move
        self.zobrist_hash ^= ZOBRIST_BLACK_TO_MOVE
        self.white_to_move = not self.white_to_move

        if self.white_to_move:
            self.full_move_number += 1

        self.move_stack.append(move)
        self._record_position()

    def undo_move(self):
        """Undo the last move."""
        if not self.move_stack:
            return None

        move = self.move_stack.pop()
        self._unrecord_position()

        fr, fc = move.from_row, move.from_col
        tr, tc = move.to_row, move.to_col
        piece = move.piece

        # Switch side back
        self.white_to_move = not self.white_to_move
        self.zobrist_hash ^= ZOBRIST_BLACK_TO_MOVE

        # Remove placed piece from destination
        placed = move.promotion if move.promotion else piece
        self._update_zobrist_piece(placed, tr, tc)

        # Restore piece at source
        self.squares[fr][fc] = piece
        self._update_zobrist_piece(piece, fr, fc)

        # Restore captured piece
        if move.captured != '.':
            if move.is_en_passant:
                cap_row = fr
                self.squares[cap_row][tc] = move.captured
                self._update_zobrist_piece(move.captured, cap_row, tc)
                self.squares[tr][tc] = '.'
            else:
                self.squares[tr][tc] = move.captured
                self._update_zobrist_piece(move.captured, tr, tc)
        else:
            self.squares[tr][tc] = '.'

        # Undo castling rook move
        if move.is_castling and move.rook_from and move.rook_to:
            rook = 'R' if self.white_to_move else 'r'
            rfr, rfc = move.rook_from
            rtr, rtc = move.rook_to
            self._update_zobrist_piece(rook, rtr, rtc)
            self.squares[rtr][rtc] = '.'
            self.squares[rfr][rfc] = rook
            self._update_zobrist_piece(rook, rfr, rfc)

        # Restore castling rights
        old_castling = (
            (self.castling_rights['K'] << 3) |
            (self.castling_rights['Q'] << 2) |
            (self.castling_rights['k'] << 1) |
            (self.castling_rights['q'])
        )
        self.zobrist_hash ^= ZOBRIST_CASTLING[old_castling]

        self.castling_rights = move.prev_castling_rights

        new_castling = (
            (self.castling_rights['K'] << 3) |
            (self.castling_rights['Q'] << 2) |
            (self.castling_rights['k'] << 1) |
            (self.castling_rights['q'])
        )
        self.zobrist_hash ^= ZOBRIST_CASTLING[new_castling]

        # Restore en passant
        if self.en_passant:
            self.zobrist_hash ^= ZOBRIST_EN_PASSANT[self.en_passant[1]]
        self.en_passant = move.prev_en_passant
        if self.en_passant:
            self.zobrist_hash ^= ZOBRIST_EN_PASSANT[self.en_passant[1]]

        # Restore clocks
        self.half_move_clock = move.prev_half_move_clock
        if not self.white_to_move:
            self.full_move_number -= 1

        self._record_position()
        return move

    def to_dict(self):
        """Serialize board state to a dictionary for API responses."""
        board_data = []
        for r in range(8):
            row = []
            for c in range(8):
                piece = self.squares[r][c]
                row.append({
                    'piece': piece,
                    'symbol': PIECE_SYMBOLS.get(piece, ''),
                    'color': 'white' if piece in WHITE_PIECES else ('black' if piece in BLACK_PIECES else None)
                })
            board_data.append(row)

        return {
            'squares': board_data,
            'whiteToMove': self.white_to_move,
            'castlingRights': self.castling_rights,
            'enPassant': list(self.en_passant) if self.en_passant else None,
            'halfMoveClock': self.half_move_clock,
            'fullMoveNumber': self.full_move_number,
            'fen': self.to_fen(),
        }

    def __repr__(self):
        lines = []
        for r in range(8):
            rank = str(8 - r) + ' '
            for c in range(8):
                p = self.squares[r][c]
                rank += (PIECE_SYMBOLS.get(p, p) if p != '.' else '·') + ' '
            lines.append(rank)
        lines.append('  a b c d e f g h')
        return '\n'.join(lines)
