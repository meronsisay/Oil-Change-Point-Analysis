import { useData } from '../context/DataContext'
import VolatilityPanel from '../components/metrics/VolatilityPanel'
import GlobalStatCard from '../components/metrics/GlobalStatCard'

export default function MetricsPage() {
  const { volatility, globalChangepoint, eventChangepoints } = useData()

  return (
    <div className="page">
      <GlobalStatCard globalChangepoint={globalChangepoint} />
      <VolatilityPanel volatility={volatility} />

      <div className="chart-card">
        <div className="chart-card-header">
          <h2>Modeled Events — Convergence &amp; Impact</h2>
          <span className="chart-card-sub">Reliability status per event's change point model</span>
        </div>
        <table className="metrics-table">
          <thead>
            <tr>
              <th>Event</th>
              <th>Detected</th>
              <th>Offset</th>
              <th>Price shift</th>
              <th>r_hat</th>
            </tr>
          </thead>
          <tbody>
            {eventChangepoints.map((cp) => (
              <tr key={cp.event_name}>
                <td>{cp.event_name}</td>
                <td className="mono">{cp.detected_date}</td>
                <td className="mono">{cp.offset_days}d</td>
                <td className={`mono ${cp.pct_change < 0 ? 'is-negative' : 'is-positive'}`}>
                  {cp.pct_change > 0 ? '+' : ''}{cp.pct_change.toFixed(1)}%
                </td>
                <td className="mono">{cp.rhat_max.toFixed(4)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
