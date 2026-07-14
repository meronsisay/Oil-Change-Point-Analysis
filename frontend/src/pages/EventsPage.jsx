import { useData } from '../context/DataContext'
import CategoryFilter from '../components/filters/CategoryFilter'
import EventList from '../components/events/EventList'
import DrilldownPanel from '../components/events/DrilldownPanel'

export default function EventsPage() {
  const {
    category, setCategory, filteredEvents, eventChangepoints,
    selectedEvent, setSelectedEvent,
  } = useData()

  const selectedChangepoint = selectedEvent
    ? eventChangepoints.find((cp) => cp.event_name === selectedEvent.event_name) || null
    : null

  return (
    <div className="page page-two-col">
      <div className="page-primary">
        <CategoryFilter category={category} onChange={setCategory} />
        <EventList
          events={filteredEvents}
          changepoints={eventChangepoints}
          selectedEvent={selectedEvent}
          onSelectEvent={setSelectedEvent}
        />
      </div>
      <div className="page-secondary">
        <DrilldownPanel
          event={selectedEvent}
          changepointMatch={selectedChangepoint}
          onClose={() => setSelectedEvent(null)}
        />
      </div>
    </div>
  )
}
