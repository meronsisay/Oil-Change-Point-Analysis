# Frontend — React Dashboard

Interactive dashboard for the Brent oil change point analysis, split into
three routed pages rather than one long scrolling page.

## Setup

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Opens on `http://localhost:3000`. **Start the Flask backend first**
(`python ../backend/app.py`) with `data/processed/` populated, or every
page will show a load error.

## Structure

```
src/
├── api.js                       # fetch helpers + nearestPricePoint()
├── App.jsx                      # router shell (nav + routes), no page logic itself
├── context/DataContext.jsx      # fetches all data once, holds filters - shared across pages
├── pages/
│   ├── OverviewPage.jsx           # "/" - just the price chart + date filter
│   ├── EventsPage.jsx             # "/events" - event list + drill-down detail
│   └── MetricsPage.jsx            # "/metrics" - volatility + convergence table
└── components/
    ├── layout/NavBar.jsx
    ├── filters/DateRangeFilter.jsx, CategoryFilter.jsx
    ├── chart/PriceChart.jsx
    ├── events/EventList.jsx, DrilldownPanel.jsx
    └── metrics/VolatilityPanel.jsx, GlobalStatCard.jsx
```

Filters and the selected event live in `DataContext`, not in any one
page — so navigating between pages never loses your date range or
resets your selection.

## The chart bug that got fixed

The price line previously looked flat and event markers clustered on the
left. Root cause: Recharts positions points on a **category** axis by
their index within each series' own data array — mixing the ~6,500-point
price line with a ~10-point event marker set on a category axis put the
two series out of sync. Fixed by converting every date to a numeric
timestamp and using a **numeric time axis** (`type="number"`,
`scale="time"`), which positions by actual value instead — so the line
and the markers always agree on where a given date sits, regardless of
how many points either series has. Verified the date→timestamp→date
round-trip and ordering with a standalone Node script before wiring it
into the component.

Also added Recharts' `<Brush>` — a draggable strip under the chart for
zooming into a sub-range, distinct from (and complementary to) the
`DateRangeFilter` date inputs, which control what's actually fetched from
the backend.

## How to check every feature works

Go through this list after `npm run dev` is up and the backend is
running:

1. **Navigation** — click Price Trend / Events / Metrics in the nav bar.
   URL should change (`/`, `/events`, `/metrics`) and the active tab
   should highlight.
2. **Date range filter** (Overview page) — change "From"/"To". The chart
   should re-fetch and redraw with the new range; event markers in range
   should update too.
3. **Brush / zoom** — drag the small strip under the main chart. The
   chart above should zoom to that sub-range without a new network
   request (it's client-side, working off already-loaded data).
4. **Reset button** — after changing the date range, click Reset; should
   return to the default 2005–2022 window.
5. **Event marker click** (Overview page) — click any flag-shaped marker
   on the chart. Should navigate to `/events` with that event already
   selected in the drill-down panel on the right.
6. **Category filter** (Events page) — change "Event type" dropdown.
   The event list should filter to only that category.
7. **Event list click** (Events page) — click any row. Drill-down panel
   should update; for the 4 modeled events (Kuwait, Lehman, OPEC, price
   war) it should show the quantified price shift; for the other 12 it
   should show the "no dedicated model was run" note instead.
8. **Close button** on the drill-down panel — should clear the selection
   back to the empty-state message.
9. **Metrics page** — volatility bars should render with the 2020-2022
   bar highlighted in red (the max). The table below should list all 4
   modeled events with their r_hat values.
10. **Responsive check** — resize the browser window (or use dev tools'
    device toolbar) below ~1024px and ~640px. Layout should collapse to
    single-column and the nav links should stretch full-width on mobile.
11. **Error state** — stop the Flask backend and refresh any page; should
    show the "Couldn't load dashboard data" screen, not a blank page or
    console-only error.

## How price and dates actually correlate on the chart

Each row from `/api/prices` is one calendar day with its closing price;
the chart's X axis is now real elapsed time (via the timestamp fix
above), so the line's shape directly reflects Brent's actual history —
climbing through the 2000s, spiking near $147 in 2008, crashing that
same year, collapsing again 2014–2016, and crashing/recovering in 2020.
Event markers are placed at each event's own date (snapped to the
nearest actual trading day, since events don't always land on one), at
that day's real price — so a marker's vertical position always matches
the line directly beneath it.
