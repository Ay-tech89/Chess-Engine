import { useChessGame } from './hooks/useChessGame';
import Chessboard from './components/Chessboard';
import GameControls from './components/GameControls';
import MoveHistory from './components/MoveHistory';
import CapturedPieces from './components/CapturedPieces';
import AIStatus from './components/AIStatus';

const PROMO_SYMBOLS = { white: ['♕', '♖', '♗', '♘'], black: ['♛', '♜', '♝', '♞'] };
const PROMO_PIECES = ['Q', 'R', 'B', 'N'];

export default function App() {
  const {
    gameState, selectedSquare, legalMoves, loading, aiThinking,
    error, difficulty, playerColor, promotionPending,
    newGame, selectSquare, makeMove, handlePromotion, cancelPromotion,
    undo, redo, changeDifficulty, changePlayerColor, clearError,
  } = useChessGame();

  // Handle drag-and-drop
  const handleDrop = (from, to) => {
    if (!gameState || gameState.gameOver || aiThinking) return;
    const piece = gameState.board.squares[from.row][from.col];
    const promoRow = playerColor === 'white' ? 0 : 7;
    if (piece.piece.toUpperCase() === 'P' && to.row === promoRow) {
      selectSquare(from.row, from.col);
      return;
    }
    makeMove(from, to);
  };

  // Determine win/loss relative to player
  const getGameOverText = () => {
    if (!gameState?.gameOver) return {};
    const result = gameState.gameResult;
    if (result === 'draw') return { title: '🤝 Draw', desc: 'The game ended in a draw.' };
    if (result === playerColor) return { title: '🏆 You Win!', desc: 'Checkmate! Brilliant game.' };
    return { title: '💀 Engine Wins', desc: 'Checkmate. Better luck next time.' };
  };

  if (loading && !gameState) {
    return (
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        height: '100vh', flexDirection: 'column', gap: 16,
      }}>
        <div className="ai-status__dot thinking" style={{ width: 24, height: 24 }} />
        <p style={{ color: 'var(--on-surface-dim)' }}>Loading Chess Engine...</p>
      </div>
    );
  }

  const gameOver = getGameOverText();

  return (
    <div className="app">
      {/* Header — Fix #2: settings icon removed */}
      <header className="header">
        <div className="header__brand">
          <span className="material-icons-round icon">token</span>
          Grandmaster Engine
        </div>
        <div />
      </header>

      {/* Left Sidebar */}
      <GameControls
        turn={gameState?.turn}
        status={gameState?.status}
        difficulty={difficulty}
        playerColor={playerColor}
        canUndo={gameState?.canUndo}
        canRedo={gameState?.canRedo}
        gameOver={gameState?.gameOver}
        aiThinking={aiThinking}
        onNewGame={newGame}
        onUndo={undo}
        onRedo={redo}
        onDifficultyChange={changeDifficulty}
        onColorChange={changePlayerColor}
      />

      {/* Center — Board */}
      <main className="board-area">
        {gameState && (
          <Chessboard
            board={gameState.board}
            selectedSquare={selectedSquare}
            legalMoves={legalMoves}
            lastMove={gameState.lastMove}
            gameOver={gameState.gameOver}
            turn={gameState.turn}
            status={gameState.status}
            playerColor={playerColor}
            onSquareClick={selectSquare}
            onDrop={handleDrop}
          />
        )}

        {/* Game over banner */}
        {gameState?.gameOver && (
          <div className="game-over-banner">
            <h2>{gameOver.title}</h2>
            <p>{gameOver.desc}</p>
            <button className="btn btn-primary" onClick={newGame}>
              <span className="material-icons-round">refresh</span>
              Play Again
            </button>
          </div>
        )}

        {/* Promotion modal */}
        {promotionPending && (
          <div className="modal-overlay" onClick={cancelPromotion}>
            <div className="promotion-modal" onClick={e => e.stopPropagation()}>
              <h3>Choose Promotion</h3>
              <div className="promotion-options">
                {PROMO_PIECES.map((piece, i) => (
                  <button
                    key={piece}
                    className="promotion-btn"
                    onClick={() => handlePromotion(piece)}
                    title={piece === 'Q' ? 'Queen' : piece === 'R' ? 'Rook' : piece === 'B' ? 'Bishop' : 'Knight'}
                  >
                    {PROMO_SYMBOLS[playerColor][i]}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Right Sidebar */}
      <aside className="sidebar-right">
        <CapturedPieces
          capturedWhite={gameState?.capturedWhite}
          capturedBlack={gameState?.capturedBlack}
        />

        <MoveHistory moves={gameState?.moveHistory} />

        <AIStatus thinking={aiThinking} searchInfo={gameState?.aiSearchInfo} />
      </aside>

      {/* Error toast */}
      {error && (
        <div style={{
          position: 'fixed', bottom: 24, left: '50%', transform: 'translateX(-50%)',
          padding: '12px 24px', borderRadius: 'var(--radius)', zIndex: 999,
          background: 'var(--error-bg)', border: '1px solid var(--error)',
          color: 'var(--error)', fontSize: 14, display: 'flex', gap: 12, alignItems: 'center',
        }}>
          <span>{error}</span>
          <button onClick={clearError} style={{
            background: 'none', border: 'none', color: 'var(--error)',
            cursor: 'pointer', fontSize: 18, lineHeight: 1,
          }}>✕</button>
        </div>
      )}
    </div>
  );
}
