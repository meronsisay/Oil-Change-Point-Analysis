# Backend — Flask API

Serves the Task 2 change point analysis results to the React dashboard.
Has no PyMC/ArviZ dependency — it only reads static files written by
`export_results_for_dashboard()` in `notebooks/change_point_model.ipynb`.

## Setup

```bash
pip install -r ../requirements.txt  
python app.py
```

Runs on `http://localhost:5000`. Requires `data/processed/` to already
exist — populate it by running `change_point_model.ipynb` end to end at
least once first.

## Endpoints

### `GET /api/health`
Checks that all expected data files are present.

**Response**
```json
{
  "data_dir": "/path/to/data/processed",
  "files": {
    "prices.csv": true,
    "global_changepoint.json": true,
    "event_changepoints.json": true,
    "events.json": true,
    "volatility.json": true
  }
}
```

### `GET /api/prices`
Historical daily Brent price series.

**Query params** (both optional)
| Param | Format | Description |
|---|---|---|
| `start` | `YYYY-MM-DD` | Only return rows on/after this date |
| `end` | `YYYY-MM-DD` | Only return rows on/before this date |

**Response** — array of `{Date, Price, log_return}`. `log_return` is
`null` for the first row (no prior day to compare against).
```json
[
  {"Date": "2020-01-01", "Price": 65.0, "log_return": null},
  {"Date": "2020-01-02", "Price": 64.5, "log_return": -0.0077}
]
```

### `GET /api/changepoints/global`
The single global change-point model's result (full 1987–2022 series).

**Response**
```json
{
  "tau_mode_date": "2005-02-23",
  "tau_hdi_dates": ["2005-02-14", "2005-03-02"],
  "mu1_mean": 21.42,
  "mu2_mean": 75.61,
  "mu1_hdi": [20.91, 21.94],
  "mu2_hdi": [75.09, 76.12],
  "pct_change_mean": 2.53,
  "rhat_max": 1.0
}
```

### `GET /api/changepoints/events`
Per-event windowed change-point results — the 4 targeted events, with
detected date, offset from the real event date, price shift, and
convergence status.

**Response**
```json
[
  {
    "event_name": "OPEC Declines to Cut Production",
    "actual_date": "2014-11-27",
    "detected_date": "2014-11-26",
    "offset_days": -1,
    "price_before": 105.09,
    "price_after": 49.17,
    "pct_change": -53.2,
    "rhat_max": 1.02,
    "matched_event": "OPEC Declines to Cut Production"
  }
]
```

### `GET /api/events`
All 16 researched events (wars, OPEC decisions, sanctions, financial
crises) — not just the 4 that were modeled. Used for the "all events"
timeline view.

**Response** — array of `{event_id, date, event_name, category, expected_direction, description}`.

### `GET /api/volatility`
Log-return volatility (standard deviation) by time period — the "key
indicator" data the dashboard displays alongside price trends.

**Response**
```json
[
  {"period": "1987-1999", "n_obs": 3200, "log_return_std": 0.023},
  {"period": "2020-2022", "n_obs": 729, "log_return_std": 0.047}
]
```

## Notes for the frontend

- All endpoints return JSON except `/api/prices`, which is generated from
  a CSV internally but still returned as JSON — no separate CSV endpoint.
- Missing files return `404` with `{"error": "..."}`, not a silent empty
  response — check `response.ok` before parsing.
- CORS is enabled for all origins via `flask-cors`, so the React dev
  server (typically `localhost:3000`) can call this API directly.