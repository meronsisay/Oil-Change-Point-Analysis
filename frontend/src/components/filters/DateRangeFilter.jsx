export default function DateRangeFilter({ dateRange, onChange, onReset }) {
  return (
    <div className="filter-bar">
      <div className="filter-group">
        <label htmlFor="start-date">From</label>
        <input
          id="start-date"
          type="date"
          value={dateRange.start}
          min="1987-05-20"
          max="2022-11-14"
          onChange={(e) => onChange({ ...dateRange, start: e.target.value })}
        />
      </div>
      <div className="filter-group">
        <label htmlFor="end-date">To</label>
        <input
          id="end-date"
          type="date"
          value={dateRange.end}
          min="1987-05-20"
          max="2022-11-14"
          onChange={(e) => onChange({ ...dateRange, end: e.target.value })}
        />
      </div>
      <button className="btn-reset" onClick={onReset} type="button">
        Reset
      </button>
    </div>
  )
}
