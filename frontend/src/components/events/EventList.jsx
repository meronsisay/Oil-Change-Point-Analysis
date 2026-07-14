export default function EventList({ events, changepoints, selectedEvent, onSelectEvent }) {
  const cpByName = Object.fromEntries(changepoints.map((cp) => [cp.event_name, cp]))

  return (
    <div className="event-list">
      <h2>Researched Events</h2>
      <ul>
        {events.map((ev) => {
          const cp = cpByName[ev.event_name]
          const isSelected = selectedEvent?.event_name === ev.event_name
          return (
            <li key={ev.event_id}>
              <button
                className={`event-list-item ${isSelected ? 'is-selected' : ''}`}
                onClick={() => onSelectEvent(ev)}
                type="button"
              >
                <span className="event-list-date mono">{ev.date}</span>
                <span className="event-list-name">{ev.event_name}</span>
                {cp && (
                  <span className={`event-list-pct mono ${cp.pct_change < 0 ? 'is-negative' : 'is-positive'}`}>
                    {cp.pct_change > 0 ? '+' : ''}{cp.pct_change.toFixed(1)}%
                  </span>
                )}
              </button>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
