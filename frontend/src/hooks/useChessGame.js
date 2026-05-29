import { useState, useCallback, useEffect, useRef } from 'react';
import { chessApi } from '../api/chessApi';

/**
 * Custom hook managing all chess game state and API interactions.
 */
export function useChessGame() {
  const [gameState, setGameState] = useState(null);
  const [selectedSquare, setSelectedSquare] = useState(null);
  const [legalMoves, setLegalMoves] = useState([]);
  const [loading, setLoading] = useState(true);
  const [aiThinking, setAiThinking] = useState(false);
  const [error, setError] = useState(null);
  const [difficulty, setDifficultyState] = useState('medium');
  const [playerColor, setPlayerColor] = useState('white');
  const [promotionPending, setPromotionPending] = useState(null);
  const moveHistoryRef = useRef(null);

  const aiColor = playerColor === 'white' ? 'black' : 'white';

  // Load initial game state
  useEffect(() => {
    loadGameState();
  }, []);

  const loadGameState = useCallback(async () => {
    try {
      setLoading(true);
      const state = await chessApi.getGameState();
      setGameState(state);
      setDifficultyState(state.difficulty || 'medium');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  /** Trigger AI to move if it's the AI's turn */
  const triggerAiIfNeeded = useCallback(async (state, aiSide) => {
    if (!state.gameOver && state.turn === aiSide) {
      setAiThinking(true);
      try {
        const aiState = await chessApi.aiMove();
        setGameState(aiState);
      } catch (err) {
        setError(err.message);
      } finally {
        setAiThinking(false);
      }
    }
  }, []);

  const newGame = useCallback(async () => {
    try {
      setLoading(true);
      setSelectedSquare(null);
      setLegalMoves([]);
      setError(null);
      setAiThinking(false);
      setPromotionPending(null);
      const state = await chessApi.newGame(difficulty);
      setGameState(state);
      setLoading(false);

      // If player is black, AI (white) moves first
      if (playerColor === 'black') {
        await triggerAiIfNeeded(state, 'white');
      }
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  }, [difficulty, playerColor, triggerAiIfNeeded]);

  const selectSquare = useCallback(async (row, col) => {
    if (!gameState || gameState.gameOver || aiThinking) return;
    if (gameState.turn !== playerColor) return; // Only allow moves on player's turn

    const piece = gameState.board.squares[row][col];

    // If clicking on own piece, select it and show legal moves
    if (piece.color === playerColor) {
      setSelectedSquare({ row, col });
      try {
        const result = await chessApi.getLegalMoves(row, col);
        setLegalMoves(result.moves || []);
      } catch (err) {
        setLegalMoves([]);
      }
      return;
    }

    // If a piece is selected and clicking a legal move destination
    if (selectedSquare) {
      const isLegal = legalMoves.find(m => m.row === row && m.col === col);
      if (isLegal) {
        // Check if this is a pawn promotion
        const selectedPiece = gameState.board.squares[selectedSquare.row][selectedSquare.col];
        const promoRow = playerColor === 'white' ? 0 : 7;
        if (selectedPiece.piece.toUpperCase() === 'P' && row === promoRow) {
          setPromotionPending({ from: selectedSquare, to: { row, col } });
          return;
        }
        await makeMove(selectedSquare, { row, col });
      } else {
        // Deselect
        setSelectedSquare(null);
        setLegalMoves([]);
      }
    }
  }, [gameState, selectedSquare, legalMoves, aiThinking, playerColor]);

  const makeMove = useCallback(async (from, to, promotion = null) => {
    try {
      setSelectedSquare(null);
      setLegalMoves([]);
      setPromotionPending(null);

      const state = await chessApi.makeMove(
        { row: from.row, col: from.col },
        { row: to.row, col: to.col },
        promotion
      );
      setGameState(state);

      // Trigger AI on the opposite color's turn
      await triggerAiIfNeeded(state, aiColor);
    } catch (err) {
      setError(err.message);
    }
  }, [aiColor, triggerAiIfNeeded]);

  const handlePromotion = useCallback(async (piece) => {
    if (!promotionPending) return;
    await makeMove(promotionPending.from, promotionPending.to, piece);
  }, [promotionPending, makeMove]);

  const cancelPromotion = useCallback(() => {
    setPromotionPending(null);
    setSelectedSquare(null);
    setLegalMoves([]);
  }, []);

  const undo = useCallback(async () => {
    if (aiThinking) return;
    try {
      const state = await chessApi.undo();
      setGameState(state);
      setSelectedSquare(null);
      setLegalMoves([]);
    } catch (err) {
      setError(err.message);
    }
  }, [aiThinking]);

  const redo = useCallback(async () => {
    if (aiThinking) return;
    try {
      const state = await chessApi.redo();
      setGameState(state);
      setSelectedSquare(null);
      setLegalMoves([]);
    } catch (err) {
      setError(err.message);
    }
  }, [aiThinking]);

  const changeDifficulty = useCallback(async (newDifficulty) => {
    try {
      await chessApi.setDifficulty(newDifficulty);
      setDifficultyState(newDifficulty);
    } catch (err) {
      setError(err.message);
    }
  }, []);

  const changePlayerColor = useCallback((color) => {
    setPlayerColor(color);
    // A new game must be started for color change to take effect
  }, []);

  const clearError = useCallback(() => setError(null), []);

  return {
    gameState,
    selectedSquare,
    legalMoves,
    loading,
    aiThinking,
    error,
    difficulty,
    playerColor,
    promotionPending,
    moveHistoryRef,
    newGame,
    selectSquare,
    makeMove,
    handlePromotion,
    cancelPromotion,
    undo,
    redo,
    changeDifficulty,
    changePlayerColor,
    clearError,
  };
}
