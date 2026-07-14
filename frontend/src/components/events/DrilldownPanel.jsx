export default function DrilldownPanel({ event, changepointMatch, onClose }) {
  if (!event) {
    return (
      <div className="drilldown-panel drilldown-empty">
        <p>Select an event marker on the chart, or an item in the list, to see its detail here.</p>
      </div>
    )
  }

  return (
    <div className="drilldown-panel">
      <div className="drilldown-header">
        <span className="drilldown-category">{event.category}</span>
        <button className="drilldown-close" onClick={onClose} aria-label="Close detail panel">
          ×
        </button>
      </div>
      <h3>{event.event_name}</h3>
      <div className="drilldown-date">{event.date}</div>
      <p className="drilldown-description">{event.description}</p>

      {changepointMatch ? (
        <div className="drilldown-quant">
          <div className="drilldown-quant-row">
            <span>Detected change point</span>
            <span className="mono">{changepointMatch.detected_date}</span>
          </div>
          <div className="drilldown-quant-row">
            <span>Offset from event date</span>
            <span className="mono">{changepointMatch.offset_days} days</span>
          </div>
          <div className="drilldown-quant-row">
            <span>Price shift</span>
            <span className="mono">
              ${changepointMatch.price_before.toFixed(2)} → ${changepointMatch.price_after.toFixed(2)}
            </span>
          </div>
          <div className={`drilldown-quant-highlight ${changepointMatch.pct_change < 0 ? 'is-negative' : 'is-positive'}`}>
            {changepointMatch.pct_change > 0 ? '+' : ''}
            {changepointMatch.pct_change.toFixed(1)}%
          </div>
        </div>
      ) : (
        <div className="drilldown-no-model">
          No dedicated change point model was run for this event — showing
          the researched event details only.
        </div>
      )}
    </div>
  )
}
