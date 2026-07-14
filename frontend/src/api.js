const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'

async function getJSON(path) {
  const res = await fetch(`${API_BASE}${path}`)
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.error || `Request to ${path} failed (${res.status})`)
  }
  return res.json()
}

export function fetchPrices({ start, end } = {}) {
  const params = new URLSearchParams()
  if (start) params.set('start', start)
  if (end) params.set('end', end)
  const qs = params.toString()
  return getJSON(`/api/prices${qs ? `?${qs}` : ''}`)
}

export const fetchGlobalChangepoint = () => getJSON('/api/changepoints/global')
export const fetchEventChangepoints = () => getJSON('/api/changepoints/events')
export const fetchEvents = () => getJSON('/api/events')
export const fetchVolatility = () => getJSON('/api/volatility')

/**
 * Event dates rarely land exactly on a trading day (weekends, holidays),
 * so plotting an event marker requires finding the closest price point
 * in the currently-loaded series rather than an exact date match.
 * Assumes `prices` is sorted ascending by Date (true for /api/prices).
 */
export function nearestPricePoint(dateStr, prices) {
  if (!prices.length) return null
  const target = new Date(dateStr).getTime()

  let lo = 0
  let hi = prices.length - 1
  while (lo < hi) {
    const mid = Math.floor((lo + hi) / 2)
    if (new Date(prices[mid].Date).getTime() < target) {
      lo = mid + 1
    } else {
      hi = mid
    }
  }

  const candidates = [prices[lo]]
  if (lo > 0) candidates.push(prices[lo - 1])

  return candidates.reduce((closest, p) =>
    Math.abs(new Date(p.Date).getTime() - target) <
    Math.abs(new Date(closest.Date).getTime() - target)
      ? p
      : closest
  )
}
