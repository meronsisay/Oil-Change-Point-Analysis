import {
  ComposedChart, Line, Scatter, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, ReferenceLine, Brush,
} from 'recharts'
import { nearestPricePoint } from '../../api'

const DIRECTION_COLOR = {
  Increase: 'var(--accent-amber)',
  Decrease: 'var(--accent-teal)',
}

const DAY_MS = 24 * 60 * 60 * 1000

function formatTick(ts) {
  return new Date(ts).toISOString().slice(0, 10)
}

function ChartTooltip({ active, payload }) {
  if (!active || !payload?.length) return null
  const point = payload[0].payload
  return (
    <div className="chart-tooltip">
      <div className="chart-tooltip-date">{point.Date}</div>
      <div className="chart-tooltip-price">${point.Price.toFixed(2)}</div>
      {point.eventName && <div className="chart-tooltip-event">{point.eventName}</div>}
    </div>
  )
}

export default function PriceChart({ prices, events, globalChangepoint, onSelectEvent }) {
  // The root cause of the earlier bug: Recharts positions points on a
  // *category* axis by their index within each series' own data array,
  // not by matching value. Mixing a ~6,500-point Line with a ~10-point
  // Scatter on a category axis made the Scatter's points land at wildly
  // wrong positions. Fix: give every point a real numeric timestamp and
  // use a numeric axis, which positions by value - so Line and Scatter
  // always agree on where a given date actually sits, regardless of how
  // many points either series has.
  const chartData = prices.map((p) => ({ ...p, ts: new Date(p.Date).getTime() }))

  const eventMarkers = events
    .map((ev) => {
      const point = nearestPricePoint(ev.date, prices)
      if (!point) return null
      return { ...point, ts: new Date(point.Date).getTime(), eventName: ev.event_name, event: ev }
    })
    .filter(Boolean)

  const domain = chartData.length
    ? [chartData[0].ts, chartData[chartData.length - 1].ts]
    : ['auto', 'auto']

  return (
    <div className="chart-card">
      <div className="chart-card-header">
        <h2>Brent Crude Price</h2>
        <span className="chart-card-sub">USD / barrel — drag the strip below to zoom a range</span>
      </div>
      <ResponsiveContainer width="100%" height={420}>
        <ComposedChart data={chartData} margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border-soft)" />
          <XAxis
            dataKey="ts"
            type="number"
            domain={domain}
            scale="time"
            tickFormatter={formatTick}
            tick={{ fill: 'var(--text-muted)', fontSize: 11, fontFamily: 'var(--font-mono)' }}
            minTickGap={50}
          />
          <YAxis
            tick={{ fill: 'var(--text-muted)', fontSize: 11, fontFamily: 'var(--font-mono)' }}
            width={48}
            domain={[(min) => Math.max(0, Math.floor(min * 0.9)), (max) => Math.ceil(max * 1.08)]}
          />
          <Tooltip content={<ChartTooltip />} />
          {globalChangepoint && (
            <ReferenceLine
              x={new Date(globalChangepoint.tau_mode_date).getTime()}
              stroke="var(--accent-red)"
              strokeDasharray="4 4"
              label={{ value: 'Global break', fill: 'var(--accent-red)', fontSize: 10, position: 'insideTopRight' }}
            />
          )}
          <Line
            type="monotone"
            dataKey="Price"
            stroke="var(--accent-amber)"
            strokeWidth={1.5}
            dot={false}
            isAnimationActive={false}
          />
          <Scatter data={eventMarkers} dataKey="Price" fill="var(--accent-teal)" shape={(props) => (
            <EventMarker {...props} onSelectEvent={onSelectEvent} />
          )} />
          <Brush
            dataKey="ts"
            height={28}
            stroke="var(--accent-amber)"
            fill="var(--surface-2)"
            tickFormatter={formatTick}
            travellerWidth={8}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}

function EventMarker({ cx, cy, payload, onSelectEvent }) {
  const color = DIRECTION_COLOR[payload.event.expected_direction] || 'var(--accent-teal)'
  return (
    <g
      className="event-marker"
      transform={`translate(${cx}, ${cy})`}
      onClick={() => onSelectEvent(payload.event)}
      tabIndex={0}
      role="button"
      aria-label={`View details for ${payload.eventName}`}
    >
      <path d="M0,-10 L4,-2 L0,0 L-4,-2 Z" fill={color} />
      <circle r={2.5} fill={color} />
    </g>
  )
}
