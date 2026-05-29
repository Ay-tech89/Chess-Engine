"""
High-level game controller.

Manages the game lifecycle: new game, making moves, undo/redo,
game status detection, and serialization for API responses.
"""

from .board import Board, Move, PIECE_SYMBOLS, WHITE_PIECES, BLACK_PIECES
from .moves import generate_legal_moves, get_legal_moves_for_square, is_in_check
from .evaluation import is_checkmate, is_stalemate, is_draw
from .search import SearchEngine


class ChessGame:
    """
    Main chess game class.

    Coordinates the board, move generation, AI search, and game state.
    """

    def __init__(self):
        self.board = Board()
        self.engine = SearchEngine()
        self.move_history = []       # List of (move, san_notation) tuples
        self.redo_stack = []         # For redo functionality
        self.captured_white = []     # White pieces captured by black
        self.captured_black = []     # Black pieces captured by white
        self.game_over = False
        self.game_result = None      # 'white', 'black', 'draw', None
        self.difficulty = 'medium'
        self.engine.set_difficulty(self.difficulty)

    def new_game(self):
        """Start a new game."""
        self.board = Board()
        self.engine = SearchEngine()
        self.engine.set_difficulty(self.difficulty)
        self.move_history = []
        self.redo_stack = []
        self.captured_white = []
        self.captured_black = []
        self.game_over = False
        self.game_result = None

    def set_difficulty(self, difficulty):
        """Set AI difficulty level."""
        self.difficulty = difficulty.lower()
        self.engine.set_difficulty(self.difficulty)

    def get_legal_moves(self, square):
        """
        Get legal moves for a piece at the given square.

        Args:
            square: String like 'e2' or tuple (row, col)

        Returns:
            List of destination squares as 'file+rank' strings (e.g., ['e3', 'e4'])
        """
        if isinstance(square, str):
            row, col = self._parse_square(square)
        else:
            row, col = square

        if row is None:
            return []

        moves = get_legal_moves_for_square(self.board, row, col)
        destinations = []
        for m in moves:
            files = 'abcdefgh'
            ranks = '87654321'
            dest = f"{files[m.to_col]}{ranks[m.to_row]}"
            destinations.append({
                'square': dest,
                'row': m.to_row,
                'col': m.to_col,
                'isCapture': m.captured != '.',
                'isPromotion': m.to_row == 0 or m.to_row == 7 and m.piece.upper() == 'P',
                'isCastling': m.is_castling,
            })

        return destinations

    def make_player_move(self, from_square, to_square, promotion=None):
        """
        Make a player's move.

        Args:
            from_square: String like 'e2' or dict {row, col}
            to_square: String like 'e4' or dict {row, col}
            promotion: Optional promotion piece ('Q', 'R', 'B', 'N')

        Returns:
            dict with updated game state, or error dict
        """
        if self.game_over:
            return {'error': 'Game is already over'}

        # Parse squares
        if isinstance(from_square, str):
            fr, fc = self._parse_square(from_square)
        else:
            fr, fc = from_square.get('row'), from_square.get('col')

        if isinstance(to_square, str):
            tr, tc = self._parse_square(to_square)
        else:
            tr, tc = to_square.get('row'), to_square.get('col')

        if fr is None or tr is None:
            return {'error': 'Invalid square'}

        # Find the matching legal move
        legal_moves = generate_legal_moves(self.board)
        matched_move = None

        for move in legal_moves:
            if move.from_row == fr and move.from_col == fc and \
               move.to_row == tr and move.to_col == tc:
                if move.promotion:
                    # Match promotion piece
                    if promotion and move.promotion.upper() == promotion.upper():
                        matched_move = move
                        break
                    elif not promotion and move.promotion.upper() == 'Q':
                        # Default to queen promotion
                        matched_move = move
                        break
                else:
                    matched_move = move
                    break

        if not matched_move:
            return {'error': 'Illegal move'}

        # Make the move
        san = matched_move.to_san(self.board)
        self.board.make_move(matched_move)

        # Track captured pieces
        if matched_move.captured != '.':
            if matched_move.captured in WHITE_PIECES:
                self.captured_white.append(matched_move.captured)
            else:
                self.captured_black.append(matched_move.captured)

        # Add check/checkmate indicator to SAN
        if is_checkmate(self.board):
            san += '#'
        elif is_in_check(self.board, self.board.white_to_move):
            san += '+'

        self.move_history.append((matched_move, san))
        self.redo_stack = []  # Clear redo stack on new move

        # Check game status
        self._update_game_status()

        return self.get_state()

    def make_ai_move(self):
        """
        Let the AI make a move.

        Returns:
            dict with updated game state
        """
        if self.game_over:
            return {'error': 'Game is already over'}

        best_move = self.engine.find_best_move(self.board)

        if best_move is None:
            self._update_game_status()
            return self.get_state()

        san = best_move.to_san(self.board)
        self.board.make_move(best_move)

        # Track captured pieces
        if best_move.captured != '.':
            if best_move.captured in WHITE_PIECES:
                self.captured_white.append(best_move.captured)
            else:
                self.captured_black.append(best_move.captured)

        # Add check/checkmate indicator to SAN
        if is_checkmate(self.board):
            san += '#'
        elif is_in_check(self.board, self.board.white_to_move):
            san += '+'

        self.move_history.append((best_move, san))
        self.redo_stack = []

        self._update_game_status()

        state = self.get_state()
        state['aiSearchInfo'] = self.engine.get_search_info()
        state['aiMove'] = {
            'from': self._square_to_str(best_move.from_row, best_move.from_col),
            'to': self._square_to_str(best_move.to_row, best_move.to_col),
            'fromRow': best_move.from_row,
            'fromCol': best_move.from_col,
            'toRow': best_move.to_row,
            'toCol': best_move.to_col,
        }
        return state

    def undo(self):
        """Undo the last move (or last two moves if playing against AI)."""
        if not self.move_history:
            return {'error': 'No moves to undo'}

        # Undo AI's move
        move, san = self.move_history.pop()
        self.redo_stack.append((move, san))
        self.board.undo_move()
        self._undo_capture(move)

        # Also undo player's move if there is one
        if self.move_history:
            move2, san2 = self.move_history.pop()
            self.redo_stack.append((move2, san2))
            self.board.undo_move()
            self._undo_capture(move2)

        self.game_over = False
        self.game_result = None
        return self.get_state()

    def redo(self):
        """Redo the last undone move(s)."""
        if not self.redo_stack:
            return {'error': 'No moves to redo'}

        # Redo player's move
        move, san = self.redo_stack.pop()
        self.board.make_move(move)
        self._redo_capture(move)
        self.move_history.append((move, san))

        # Redo AI's move if available
        if self.redo_stack:
            move2, san2 = self.redo_stack.pop()
            self.board.make_move(move2)
            self._redo_capture(move2)
            self.move_history.append((move2, san2))

        self._update_game_status()
        return self.get_state()

    def _undo_capture(self, move):
        """Reverse capture tracking for undo."""
        if move.captured != '.':
            if move.captured in WHITE_PIECES:
                if self.captured_white:
                    self.captured_white.pop()
            else:
                if self.captured_black:
                    self.captured_black.pop()

    def _redo_capture(self, move):
        """Re-apply capture tracking for redo."""
        if move.captured != '.':
            if move.captured in WHITE_PIECES:
                self.captured_white.append(move.captured)
            else:
                self.captured_black.append(move.captured)

    def _update_game_status(self):
        """Check and update game-over conditions."""
        if is_checkmate(self.board):
            self.game_over = True
            self.game_result = 'black' if self.board.white_to_move else 'white'
        elif is_draw(self.board):
            self.game_over = True
            self.game_result = 'draw'

    def get_status(self):
        """Get current game status string."""
        if self.game_over:
            if self.game_result == 'white':
                return 'checkmate_white'
            elif self.game_result == 'black':
                return 'checkmate_black'
            else:
                return 'draw'

        if is_in_check(self.board, self.board.white_to_move):
            return 'check'

        return 'playing'

    def get_state(self):
        """Get the full game state as a JSON-serializable dict."""
        # Format move history for display
        formatted_moves = []
        for i in range(0, len(self.move_history), 2):
            move_num = i // 2 + 1
            white_san = self.move_history[i][1] if i < len(self.move_history) else ''
            black_san = self.move_history[i + 1][1] if i + 1 < len(self.move_history) else ''
            formatted_moves.append({
                'number': move_num,
                'white': white_san,
                'black': black_san,
            })

        # Last move highlight
        last_move = None
        if self.move_history:
            lm = self.move_history[-1][0]
            last_move = {
                'fromRow': lm.from_row, 'fromCol': lm.from_col,
                'toRow': lm.to_row, 'toCol': lm.to_col,
            }

        return {
            'board': self.board.to_dict(),
            'turn': 'white' if self.board.white_to_move else 'black',
            'status': self.get_status(),
            'gameOver': self.game_over,
            'gameResult': self.game_result,
            'moveHistory': formatted_moves,
            'capturedWhite': [PIECE_SYMBOLS.get(p, p) for p in self.captured_white],
            'capturedBlack': [PIECE_SYMBOLS.get(p, p) for p in self.captured_black],
            'lastMove': last_move,
            'difficulty': self.difficulty,
            'moveCount': len(self.move_history),
            'canUndo': len(self.move_history) > 0,
            'canRedo': len(self.redo_stack) > 0,
        }

    def _parse_square(self, square_str):
        """Parse a square string like 'e2' to (row, col)."""
        if len(square_str) != 2:
            return None, None
        file_idx = ord(square_str[0].lower()) - ord('a')
        rank_idx = 8 - int(square_str[1])
        if 0 <= file_idx < 8 and 0 <= rank_idx < 8:
            return rank_idx, file_idx
        return None, None

    def _square_to_str(self, row, col):
        """Convert (row, col) to square string like 'e2'."""
        files = 'abcdefgh'
        ranks = '87654321'
        return f"{files[col]}{ranks[row]}"
