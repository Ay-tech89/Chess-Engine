/**
 * Left sidebar — game controls, status, difficulty, color selection, timers, and action buttons.
 */
export default function GameControls({
  turn, status, difficulty, canUndo, canRedo, gameOver, aiThinking,
  playerColor,
  onNewGame, onUndo, onRedo, onDifficultyChange, onColorChange,
}) {
  const statusLabels = {
    playing: 'Playing',
    check: 'Check!',
    checkmate_white: 'Checkmate — White Wins',
    checkmate_black: 'Checkmate — Black Wins',
    draw: 'Draw',
  };

  const statusClass = status?.startsWith('checkmate') ? 'checkmate' : status;
  const isPlayerTurn = turn === playerColor;

  return (
    <aside className="sidebar-left" id="game-controls">
      {/* Title */}
      <div className="game-title">
        <span className="material-icons-round icon">smart_toy</span>
        Chess Engine
        <span className="badge">AI</span>
      </div>

      {/* Turn indicator */}
      <div className="turn-indicator" key={turn}>
        <div className={`turn-dot ${turn}`} />
        <span>{turn === 'black' ? 'Black to Move' : 'White to Move'}</span>
      </div>

      {/* Status */}
      <div>
        <div className="field-label">Status</div>
        <div className={`status-badge ${statusClass || 'playing'}`}>
          <span className="material-icons-round" style={{ fontSize: 14 }}>
            {status === 'check' ? 'warning' :
             status?.startsWith('checkmate') ? 'emoji_events' :
             status === 'draw' ? 'handshake' : 'play_circle'}
          </span>
          {statusLabels[status] || 'Playing'}
        </div>
      </div>

      {/* Play As selector */}
      <div className="field-group">
        <label className="field-label">Play As</label>
        <div className="color-selector">
          <button
            className={`color-btn ${playerColor === 'white' ? 'active' : ''}`}
            onClick={() => onColorChange('white')}
            disabled={aiThinking}
          >
            <span style={{ fontSize: 18 }}>♔</span> White
          </button>
          <button
            className={`color-btn ${playerColor === 'black' ? 'active' : ''}`}
            onClick={() => onColorChange('black')}
            disabled={aiThinking}
          >
            <span style={{ fontSize: 18 }}>♚</span> Black
          </button>
        </div>
      </div>

      {/* Difficulty */}
      <div className="field-group">
        <label className="field-label" htmlFor="difficulty-select">Engine Difficulty</label>
        <div className="select-wrapper">
          <select
            id="difficulty-select"
            value={difficulty}
            onChange={(e) => onDifficultyChange(e.target.value)}
            disabled={aiThinking}
          >
            <option value="easy">Easy</option>
            <option value="medium">Medium</option>
            <option value="hard">Hard</option>
            <option value="expert">Expert</option>
          </select>
        </div>
      </div>

      {/* Player info */}
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}>
        <div className={`player-card ${isPlayerTurn ? 'active' : ''}`}>
          <div className="field-label" style={{ marginBottom: 4 }}>You</div>
          <div style={{ fontSize: 22, fontFamily: 'var(--font-mono)', fontWeight: 700 }}>
            {playerColor === 'white' ? '♔' : '♚'}
          </div>
        </div>
        <div className={`player-card ${!isPlayerTurn ? 'active' : ''}`}>
          <div className="field-label" style={{ marginBottom: 4 }}>Engine</div>
          <div style={{ fontSize: 22, fontFamily: 'var(--font-mono)', fontWeight: 700 }}>
            {playerColor === 'white' ? '♚' : '♔'}
          </div>
        </div>
      </div>

      {/* Spacer */}
      <div style={{ flex: 1 }} />

      {/* Action buttons */}
      <button className="btn btn-primary" onClick={onNewGame} disabled={aiThinking} id="new-game-btn">
        <span className="material-icons-round">refresh</span>
        New Game
      </button>

      <div className="btn-group">
        <button className="btn btn-ghost" onClick={onUndo}
          disabled={!canUndo || aiThinking || gameOver} id="undo-btn" style={{ flex: 1 }}>
          <span className="material-icons-round">undo</span>
          Undo
        </button>
        <button className="btn btn-ghost" onClick={onRedo}
          disabled={!canRedo || aiThinking || gameOver} id="redo-btn" style={{ flex: 1 }}>
          <span className="material-icons-round">redo</span>
          Redo
        </button>
      </div>
    </aside>
  );
}
