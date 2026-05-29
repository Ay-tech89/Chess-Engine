import { useEffect, useRef } from 'react';

/**
 * Move history panel — shows algebraic notation split into White/Black columns.
 */
export default function MoveHistory({ moves }) {
  const listRef = useRef(null);

  // Auto-scroll to latest move
  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight;
    }
  }, [moves]);

  return (
    <div className="move-history" id="move-history">
      <div className="move-history__header">
        <span className="section-title" style={{ minWidth: 28 }}>#</span>
        <span className="section-title" style={{ flex: 1 }}>White Moves</span>
        <span className="section-title" style={{ flex: 1 }}>Black Moves</span>
      </div>

      <div className="move-history__list" ref={listRef}>
        {(!moves || moves.length === 0) ? (
          <div className="move-history__empty">
            No moves yet — make your first move!
          </div>
        ) : (
          moves.map((move, idx) => (
            <div
              key={idx}
              className={`move-row ${idx === moves.length - 1 ? 'current' : ''}`}
            >
              <span className="move-num">{move.number}.</span>
              <span className="move-white">{move.white || ''}</span>
              <span className="move-black">{move.black || ''}</span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
