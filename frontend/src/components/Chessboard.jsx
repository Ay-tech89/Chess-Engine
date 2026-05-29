import { useState, useCallback } from 'react';

/**
 * Interactive 8x8 chessboard with click-to-move and drag-and-drop.
 * Supports board flipping when player plays as black.
 */
export default function Chessboard({
  board, selectedSquare, legalMoves, lastMove, gameOver,
  turn, onSquareClick, onDrop, status, playerColor,
}) {
  const [dragFrom, setDragFrom] = useState(null);
  const flipped = playerColor === 'black';

  const isSelected = (r, c) =>
    selectedSquare && selectedSquare.row === r && selectedSquare.col === c;

  const isLegalMove = (r, c) =>
    legalMoves.some(m => m.row === r && m.col === c);

  const isLegalCapture = (r, c) =>
    legalMoves.some(m => m.row === r && m.col === c && m.isCapture);

  const isLastMove = (r, c) =>
    lastMove && ((lastMove.fromRow === r && lastMove.fromCol === c) ||
                 (lastMove.toRow === r && lastMove.toCol === c));

  const isKingInCheck = (r, c, square) => {
    if (status !== 'check' && !status?.startsWith('checkmate')) return false;
    const piece = square.piece;
    if (piece === 'K' && turn === 'white') return true;
    if (piece === 'k' && turn === 'black') return true;
    return false;
  };

  const handleDragStart = useCallback((e, r, c, piece) => {
    if (gameOver || turn !== playerColor || piece.color !== playerColor) {
      e.preventDefault();
      return;
    }
    setDragFrom({ row: r, col: c });
    e.dataTransfer.setData('text/plain', `${r},${c}`);
    e.dataTransfer.effectAllowed = 'move';
    onSquareClick(r, c);
  }, [gameOver, turn, playerColor, onSquareClick]);

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  }, []);

  const handleDrop = useCallback((e, r, c) => {
    e.preventDefault();
    if (dragFrom && onDrop) {
      onDrop(dragFrom, { row: r, col: c });
    }
    setDragFrom(null);
  }, [dragFrom, onDrop]);

  const handleDragEnd = useCallback(() => {
    setDragFrom(null);
  }, []);

  if (!board) return null;

  // Build row/col iteration order based on flip
  const rowOrder = flipped ? [7, 6, 5, 4, 3, 2, 1, 0] : [0, 1, 2, 3, 4, 5, 6, 7];
  const colOrder = flipped ? [7, 6, 5, 4, 3, 2, 1, 0] : [0, 1, 2, 3, 4, 5, 6, 7];
  const rankLabels = flipped ? ['1', '2', '3', '4', '5', '6', '7', '8'] : ['8', '7', '6', '5', '4', '3', '2', '1'];
  const fileLabels = flipped ? ['h', 'g', 'f', 'e', 'd', 'c', 'b', 'a'] : ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'];

  return (
    <div className="chessboard-wrapper">
      <div className="chessboard-container">
        {/* Rank labels */}
        <div className="rank-labels">
          {rankLabels.map(r => <span key={r}>{r}</span>)}
        </div>

        {/* Board grid */}
        <div className="chessboard" id="chessboard">
          {rowOrder.map(r =>
            colOrder.map(c => {
              const square = board.squares[r][c];
              const isLight = (r + c) % 2 === 0;
              const selected = isSelected(r, c);
              const legal = isLegalMove(r, c);
              const capture = isLegalCapture(r, c);
              const last = isLastMove(r, c);
              const check = isKingInCheck(r, c, square);
              const isDragging = dragFrom?.row === r && dragFrom?.col === c;

              const classes = [
                'square',
                isLight ? 'light' : 'dark',
                selected && 'selected',
                legal && !capture && 'legal-move',
                capture && 'legal-capture',
                last && 'last-move',
                check && 'check',
              ].filter(Boolean).join(' ');

              const allFiles = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'];
              const allRanks = ['8', '7', '6', '5', '4', '3', '2', '1'];

              return (
                <div
                  key={`${r}-${c}`}
                  className={classes}
                  id={`square-${allFiles[c]}${allRanks[r]}`}
                  onClick={() => onSquareClick(r, c)}
                  onDragOver={handleDragOver}
                  onDrop={(e) => handleDrop(e, r, c)}
                >
                  {square.piece !== '.' && (
                    <span
                      className={`piece ${square.color}-piece ${isDragging ? 'dragging' : ''}`}
                      draggable
                      onDragStart={(e) => handleDragStart(e, r, c, square)}
                      onDragEnd={handleDragEnd}
                    >
                      {square.symbol}
                    </span>
                  )}
                </div>
              );
            })
          )}
        </div>

        {/* File labels */}
        <div className="file-labels">
          {fileLabels.map(f => <span key={f}>{f}</span>)}
        </div>
      </div>
    </div>
  );
}
