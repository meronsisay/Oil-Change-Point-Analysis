import { NavLink } from 'react-router-dom'

export default function NavBar() {
  return (
    <nav className="nav-bar">
      <div className="nav-brand">
        <span className="nav-brand-title">Brent Crude Dashboard</span>
        <span className="nav-brand-sub">Birhan Energies</span>
      </div>
      <div className="nav-links">
        <NavLink to="/" end className={({ isActive }) => `nav-link ${isActive ? 'is-active' : ''}`}>
          Price Trend
        </NavLink>
        <NavLink to="/events" className={({ isActive }) => `nav-link ${isActive ? 'is-active' : ''}`}>
          Events
        </NavLink>
        <NavLink to="/metrics" className={({ isActive }) => `nav-link ${isActive ? 'is-active' : ''}`}>
          Metrics
        </NavLink>
      </div>
    </nav>
  )
}
