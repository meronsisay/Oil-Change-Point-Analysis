# Change Point Analysis of Brent Oil Prices

**Birhan Energies — Data Science Challenge**

## Purpose

Analyze how major geopolitical events, OPEC policy decisions, and economic
shocks have affected Brent crude oil prices (daily, 1987–2022), using
Bayesian change point detection to identify structural breaks and quantify
their impact. Outputs support investors, policymakers, and energy companies
in understanding and reacting to oil market volatility.

### Foundation & Planning
- Documented the end-to-end analysis workflow, from data loading through
  Bayesian modeling to stakeholder reporting.
- Checked the raw dataset directly: 9,011 daily prices, 20-May-1987 to
  14-Nov-2022, no missing values or duplicate dates (two date formats
  present — handled explicitly in preprocessing).
- Compiled `data/events.csv`: 16 researched, source-verified key events
  (wars, OPEC decisions, sanctions, financial crises) for later comparison
  against detected change points.
- Documented assumptions, limitations, and the correlation-vs-causation
  distinction the analysis must respect.

See `notebooks/README.md` for the full workflow write-up.

### Exploratory Data Analysis
Findings from `notebooks/eda.ipynb`:
- **Trend** — price moves through several distinct multi-year regimes
  (1990s low band, 2003–2008 run-up to ~$147, 2008 crash, 2014–2016
  collapse, 2020 crash/recovery) rather than following one consistent trend.
- **Stationarity** — **price is non-stationary** (ADF stat -1.99, p=0.29);
  **log returns are stationary** (ADF stat -16.43, p≈0.0000).
- **Volatility clusters** — daily log-return std is ~0.019–0.024 through
  2019, then roughly **doubles to ~0.047 in 2020–2022**, flagging 2020 as
  a strong candidate change point ahead of the modeling stage.

### Change Point Modeling
Bayesian single change-point model (PyMC), documented in
`notebooks/change_point_model.ipynb`:
- **Global model** (full 1987–2022 series): detects its dominant break on
  2005-02-23 (mean price $21.42 → $75.61, +253%), with clean convergence
  (r_hat = 1.00). No event matches within 90 days — this reflects the
  series' long secular 2003–2008 price run-up rather than a discrete
  event, since a single break tends to land near the data's temporal
  midpoint on trending series like this.
- **Targeted windows** around 4 known events, to get per-event quantified
  impact and satisfy the "associate changes with causes" requirement the
  global model alone couldn't:

  | Event | Detected date | Offset | Price shift | Reliable? |
  |---|---|---|---|---|
  | Iraqi Invasion of Kuwait (1990-08-02) | 1990-08-01 | -1 day | $18.14 → $23.23 (+28.1%) | ✅ |
  | Lehman Brothers Collapse (2008-09-15) | 2008-10-09 | +24 days | $93.29 → $62.06 (-33.5%) | ✅ |
  | OPEC Declines to Cut Production (2014-11-27) | 2014-11-26 | -1 day | $105.09 → $49.17 (-53.2%) | ✅ (after resampling) |
  | Saudi-Russia Price War (2020-03-08) | 2020-01-29 | -39 days | $65.74 → $51.52 (-21.6%) | ✅ (after resampling) |

- **Reliability checks**: every event checked against r_hat/ESS
  thresholds (`diagnose_reliability`); 2 of 4 initially failed and were
  automatically resampled with more draws until they passed. The 2014
  result was also confirmed stable across different window sizes
  (±14 days spread).
- 1990 and 2014 detected dates land within 1 day of the real event —
  strong evidence the model found those events specifically, not just a
  nearby coincidental break.

### Exported Dashboard Data

| File | Contents |
|---|---|
| `prices.csv` | Full price series: `Date`, `Price`, `log_return` (9,011 rows) |
| `global_changepoint.json` | The global model's result: detected date, HDI, regime means |
| `event_changepoints.json` | The 4-event summary table (dates, offsets, price shift, r_hat) |
| `events.json` | All 16 researched events, for the "all events" dashboard view |

`data/processed/` is gitignored, same as `data/raw/` — it's regenerable
output, not something to hand-maintain. Re-run the notebook's export cell
any time the model changes; the backend picks up new files on the next
request with no restart needed.

## Folder Structure

```
├── .github/workflows/       # CI (unit tests on push/PR)
├── .vscode/                  # Editor settings
├── backend/
│   └── app.py                 # Flask API serving data/processed/ (no PyMC dependency)
├── data/
│   ├── raw/                    # Original source data (gitignored)
│   ├── processed/               # Exported dashboard data (gitignored, regenerable)
│   └── events.csv             # Curated key-events dataset
├── notebooks/
│   ├── README.md               # Analysis workflow, assumptions, limitations
│   ├── eda.ipynb               # Exploratory data analysis notebook
│   └── change_point_model.ipynb # Bayesian change point modeling notebook
├── scripts/                  # Standalone scripts
├── src/
│   ├── data_loader.py         # Data loading, validation, and derived columns
│   └── changepoint_model.py   # Change point model, diagnostics, event matching, export
├── tests/
│   ├── test_data_loader.py       # Unit tests for the data loader
│   └── test_changepoint_model.py # Unit tests for PyMC-independent helpers
├── requirements.txt
└── README.md
```

## Environment Setup

Requires **Python 3.11**.

```bash
git clone https://github.com/meronsisay/Oil-Change-Point-Analysis
cd Oil-Change-Point-Analysis

python3.11 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\Activate.ps1

pip install --upgrade pip
pip install -r requirements.txt
```

Place the raw price file at `data/raw/BrentOilPrices.csv` before running any
notebooks or scripts. Then run `notebooks/change_point_model.ipynb` end to
end at least once to populate `data/processed/` before starting the
backend (`python backend/app.py`).