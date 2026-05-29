# ♟ Chess Engine with AI (Alpha-Beta Pruning)

A full-stack chess application with an AI opponent powered by **Minimax + Alpha-Beta Pruning**, featuring a premium dark-themed UI designed with Google Stitch.

## Features

### Chess Engine (Python)
- ✅ Complete legal move generation for all pieces
- ✅ Castling (kingside + queenside), en passant, pawn promotion
- ✅ Check, checkmate, stalemate, draw detection
- ✅ 50-move rule and threefold repetition
- ✅ Insufficient material detection

### AI Search
- ✅ Negamax with Alpha-Beta Pruning
- ✅ Iterative Deepening
- ✅ Quiescence Search (captures)
- ✅ Transposition Table (Zobrist hashing)
- ✅ Move Ordering: MVV-LVA, Killer Moves, History Heuristic
- ✅ Piece-Square Tables (middlegame + endgame)
- ✅ Tapered Evaluation
- ✅ Adjustable difficulty (Easy → Expert)

### Frontend (React)
- ✅ Premium dark "Midnight Grandmaster" theme (Stitch-designed)
- ✅ Interactive chessboard with click & drag-and-drop
- ✅ Legal move highlighting (green dots)
- ✅ Last move highlighting
- ✅ Check indication (red glow)
- ✅ Move history in algebraic notation
- ✅ Captured pieces display
- ✅ Undo/Redo functionality
- ✅ AI thinking indicator
- ✅ Pawn promotion modal
- ✅ Game over banner
- ✅ Responsive design

---

## Quick Start

### Prerequisites
- Python 3.8+
- Node.js 18+
- npm

### 1. Start the Backend

```bash
cd backend
pip install -r requirements.txt
python app.py
```

The Flask API starts on `http://localhost:5000`.

### 2. Start the Frontend

```bash
cd frontend
npm install
npm run dev
```

The React app starts on `http://localhost:5173` and proxies API requests to the backend.

### 3. Play!

Open `http://localhost:5173` in your browser. You play as White — click or drag pieces to move. The AI responds automatically as Black.

---

## Project Structure

```
Chess Engine with AI/
├── backend/
│   ├── app.py                    # Flask API (8 endpoints)
│   ├── requirements.txt
│   └── chess_engine/
│       ├── __init__.py
│       ├── board.py              # Board representation + Zobrist hashing
│       ├── moves.py              # Legal move generation + ordering
│       ├── evaluation.py         # Position evaluation + PST
│       ├── search.py             # AI: Alpha-Beta + TT + iterative deepening
│       └── game.py               # Game controller
│
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── main.jsx
│       ├── index.css             # Design system (Stitch tokens)
│       ├── App.jsx               # Root layout
│       ├── api/
│       │   └── chessApi.js       # API client
│       ├── hooks/
│       │   └── useChessGame.js   # Game state hook
│       └── components/
│           ├── Chessboard.jsx    # Interactive board
│           ├── GameControls.jsx  # Left sidebar controls
│           ├── MoveHistory.jsx   # Move notation list
│           ├── CapturedPieces.jsx
│           └── AIStatus.jsx      # AI thinking indicator
│
└── README.md
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/new-game` | Start a new game |
| GET | `/api/game-state` | Get current board state |
| POST | `/api/move` | Make a player move |
| POST | `/api/ai-move` | Trigger AI move |
| GET | `/api/legal-moves` | Get legal moves for a square |
| POST | `/api/undo` | Undo last move pair |
| POST | `/api/redo` | Redo undone moves |
| POST | `/api/set-difficulty` | Set AI difficulty |

## Difficulty Levels

| Level | Search Depth | Approximate Strength |
|-------|-------------|---------------------|
| Easy | 2 | ~800 ELO |
| Medium | 3 | ~1200 ELO |
| Hard | 4 | ~1500 ELO |
| Expert | 5 | ~1800 ELO |
