import { useNavigate } from 'react-router-dom'
import { useData } from '../context/DataContext'
import DateRangeFilter from '../components/filters/DateRangeFilter'
import PriceChart from '../components/chart/PriceChart'

export default function OverviewPage() {
  const navigate = useNavigate()
  const {
    dateRange, setDateRange, resetFilters,
    prices, pricesLoading, filteredEvents, globalChangepoint,
    setSelectedEvent,
  } = useData()

  const globalInRange =
    globalChangepoint &&
    globalChangepoint.tau_mode_date >= dateRange.start &&
    globalChangepoint.tau_mode_date <= dateRange.end
      ? globalChangepoint
      : null

  function handleSelectEvent(event) {
    setSelectedEvent(event)
    navigate('/events')
  }

  return (
    <div className="page">
      <DateRangeFilter dateRange={dateRange} onChange={setDateRange} onReset={resetFilters} />
      {pricesLoading ? (
        <div className="chart-card chart-loading">Loading price data…</div>
      ) : (
        <PriceChart
          prices={prices}
          events={filteredEvents}
          globalChangepoint={globalInRange}
          onSelectEvent={handleSelectEvent}
        />
      )}
      <p className="page-hint">
        Click any marker to jump to its full detail on the <strong>Events</strong> page.
      </p>
    </div>
  )
}
