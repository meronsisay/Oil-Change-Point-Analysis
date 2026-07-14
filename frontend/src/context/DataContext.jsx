import { createContext, useContext, useState, useEffect, useMemo } from 'react'
import {
  fetchPrices, fetchGlobalChangepoint, fetchEventChangepoints,
  fetchEvents, fetchVolatility,
} from '../api'

const DataContext = createContext(null)

const DEFAULT_RANGE = { start: '2005-01-01', end: '2022-11-14' }

export function DataProvider({ children }) {
  const [dateRange, setDateRange] = useState(DEFAULT_RANGE)
  const [category, setCategory] = useState('All')
  const [selectedEvent, setSelectedEvent] = useState(null)

  const [prices, setPrices] = useState([])
  const [events, setEvents] = useState([])
  const [eventChangepoints, setEventChangepoints] = useState([])
  const [globalChangepoint, setGlobalChangepoint] = useState(null)
  const [volatility, setVolatility] = useState([])

  const [pricesLoading, setPricesLoading] = useState(true)
  const [error, setError] = useState(null)

  // Static data - doesn't depend on filters, fetched once regardless of
  // which page is active, so switching pages never re-fetches it.
  useEffect(() => {
    Promise.all([fetchEvents(), fetchEventChangepoints(), fetchGlobalChangepoint(), fetchVolatility()])
      .then(([ev, cps, global, vol]) => {
        setEvents(ev)
        setEventChangepoints(cps)
        setGlobalChangepoint(global)
        setVolatility(vol)
      })
      .catch((err) => setError(err.message))
  }, [])

  // Price data depends on the date range filter
  useEffect(() => {
    setPricesLoading(true)
    fetchPrices(dateRange)
      .then(setPrices)
      .catch((err) => setError(err.message))
      .finally(() => setPricesLoading(false))
  }, [dateRange])

  const filteredEvents = useMemo(() => {
    const byCategory = category === 'All' ? events : events.filter((ev) => ev.category === category)
    return byCategory.filter((ev) => ev.date >= dateRange.start && ev.date <= dateRange.end)
  }, [events, category, dateRange])

  const value = {
    dateRange, setDateRange,
    category, setCategory,
    selectedEvent, setSelectedEvent,
    prices, pricesLoading,
    events, filteredEvents,
    eventChangepoints,
    globalChangepoint,
    volatility,
    error,
    resetFilters: () => {
      setDateRange(DEFAULT_RANGE)
      setCategory('All')
      setSelectedEvent(null)
    },
  }

  return <DataContext.Provider value={value}>{children}</DataContext.Provider>
}

export function useData() {
  const ctx = useContext(DataContext)
  if (!ctx) throw new Error('useData must be used within a DataProvider')
  return ctx
}
