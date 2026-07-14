import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'

export default function VolatilityPanel({ volatility }) {
  const maxStd = Math.max(...volatility.map((v) => v.log_return_std || 0))

  return (
    <div className="chart-card">
      <div className="chart-card-header">
        <h2>Volatility by Period</h2>
        <span className="chart-card-sub">Daily log-return standard deviation</span>
      </div>
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={volatility} margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border-soft)" />
          <XAxis dataKey="period" tick={{ fill: 'var(--text-muted)', fontSize: 11, fontFamily: 'var(--font-mono)' }} />
          <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 11, fontFamily: 'var(--font-mono)' }} width={40} />
          <Tooltip
            formatter={(value) => (value == null ? 'no data' : value.toFixed(4))}
            contentStyle={{ background: 'var(--surface-2)', border: '1px solid var(--border-soft)', borderRadius: 6 }}
            labelStyle={{ color: 'var(--text-primary)' }}
          />
          <Bar dataKey="log_return_std" radius={[3, 3, 0, 0]}>
            {volatility.map((entry, i) => (
              <Cell
                key={i}
                fill={entry.log_return_std === maxStd ? 'var(--accent-red)' : 'var(--accent-teal)'}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
