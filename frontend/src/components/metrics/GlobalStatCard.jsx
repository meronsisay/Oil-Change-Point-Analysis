export default function GlobalStatCard({ globalChangepoint }) {
  if (!globalChangepoint) return null
  const dateOnly = globalChangepoint.tau_mode_date.slice(0, 10)
  return (
    <div className="stat-card">
      <span className="stat-label">Dominant structural break (full series)</span>
      <span className="stat-value mono">{dateOnly}</span>
      <span className="stat-detail mono">
        ${globalChangepoint.mu1_mean.toFixed(2)} → ${globalChangepoint.mu2_mean.toFixed(2)}
        {' '}({globalChangepoint.pct_change_mean > 0 ? '+' : ''}{(globalChangepoint.pct_change_mean * 100).toFixed(0)}%)
      </span>
    </div>
  )
}
