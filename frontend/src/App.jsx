import { Routes, Route } from 'react-router-dom'
import { DataProvider, useData } from './context/DataContext'
import NavBar from './components/layout/NavBar'
import OverviewPage from './pages/OverviewPage'
import EventsPage from './pages/EventsPage'
import MetricsPage from './pages/MetricsPage'

function AppShell() {
  const { error } = useData()

  if (error) {
    return (
      <div className="app-error">
        <h1>Couldn't load dashboard data</h1>
        <p>{error}</p>
        <p className="app-error-hint">
          Confirm the Flask backend is running and that <code>data/processed/</code>
          {' '}has been populated by running the change point notebook's export cell.
        </p>
      </div>
    )
  }

  return (
    <div className="app">
      <NavBar />
      <Routes>
        <Route path="/" element={<OverviewPage />} />
        <Route path="/events" element={<EventsPage />} />
        <Route path="/metrics" element={<MetricsPage />} />
      </Routes>
    </div>
  )
}

export default function App() {
  return (
    <DataProvider>
      <AppShell />
    </DataProvider>
  )
}
