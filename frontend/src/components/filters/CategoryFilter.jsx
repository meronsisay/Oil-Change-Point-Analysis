const CATEGORIES = ['All', 'Conflict', 'Economic Shock', 'OPEC Policy', 'Sanctions', 'Geopolitical', 'Market Structure']

export default function CategoryFilter({ category, onChange }) {
  return (
    <div className="filter-bar">
      <div className="filter-group">
        <label htmlFor="category">Event type</label>
        <select id="category" value={category} onChange={(e) => onChange(e.target.value)}>
          {CATEGORIES.map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
      </div>
    </div>
  )
}
