/**
 * AI thinking indicator — only visible when the engine is calculating.
 */
export default function AIStatus({ thinking, searchInfo }) {
  if (!thinking) return null;

  return (
    <div className="ai-status" id="ai-status">
      <div className="ai-status__header">
        <div className="ai-status__dot thinking" />
        <span>Engine calculating...</span>
      </div>

      <div className="ai-status__bar">
        <div className="ai-status__bar-fill thinking" style={{ width: '40%' }} />
      </div>
    </div>
  );
}
