/**
 * Captured pieces display — shows pieces taken by each side.
 */
export default function CapturedPieces({ capturedWhite, capturedBlack }) {
  return (
    <div className="captured-section" id="captured-pieces">
      <div className="section-header">
        <span className="section-title">Captured Pieces</span>
      </div>

      <div className="captured-row" style={{ marginBottom: 6 }}>
        <span className="label">Black:</span>
        {capturedBlack && capturedBlack.length > 0 ? (
          capturedBlack.map((p, i) => (
            <span key={i} className="captured-piece">{p}</span>
          ))
        ) : (
          <span style={{ fontSize: 12, color: 'var(--on-surface-dim)' }}>—</span>
        )}
      </div>

      <div className="captured-row">
        <span className="label">White:</span>
        {capturedWhite && capturedWhite.length > 0 ? (
          capturedWhite.map((p, i) => (
            <span key={i} className="captured-piece">{p}</span>
          ))
        ) : (
          <span style={{ fontSize: 12, color: 'var(--on-surface-dim)' }}>—</span>
        )}
      </div>
    </div>
  );
}
