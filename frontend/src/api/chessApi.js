/**
 * Chess API client — communicates with the Flask backend.
 */

const BASE_URL = import.meta.env.PROD ? '/_/backend/api' : '/api';

async function request(endpoint, options = {}) {
  const url = `${BASE_URL}${endpoint}`;
  const config = {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  };

  const response = await fetch(url, config);
  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.error || `Request failed: ${response.status}`);
  }

  return data;
}

export const chessApi = {
  /** Start a new game */
  newGame: (difficulty) =>
    request('/new-game', {
      method: 'POST',
      body: JSON.stringify({ difficulty }),
    }),

  /** Get current game state */
  getGameState: () => request('/game-state'),

  /** Make a player move */
  makeMove: (from, to, promotion) =>
    request('/move', {
      method: 'POST',
      body: JSON.stringify({ from, to, promotion }),
    }),

  /** Trigger AI to move */
  aiMove: () =>
    request('/ai-move', { method: 'POST' }),

  /** Get legal moves for a square */
  getLegalMoves: (row, col) =>
    request(`/legal-moves?row=${row}&col=${col}`),

  /** Undo last move pair */
  undo: () => request('/undo', { method: 'POST' }),

  /** Redo last undone move pair */
  redo: () => request('/redo', { method: 'POST' }),

  /** Set AI difficulty */
  setDifficulty: (difficulty) =>
    request('/set-difficulty', {
      method: 'POST',
      body: JSON.stringify({ difficulty }),
    }),
};
