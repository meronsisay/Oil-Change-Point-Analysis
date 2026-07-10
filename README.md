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


## Folder Structure

```
├── .github/workflows/       # CI (unit tests on push/PR)
├── .vscode/                  # Editor settings
├── data/
│   ├── raw/                    # Original source data (gitignored)
│   └── events.csv             # Curated key-events dataset
├── notebooks/
│   ├── README.md               # Analysis workflow, assumptions, limitations
│   └── eda.ipynb        # Exploratory data analysis notebook
├── scripts/                  # Standalone scripts
├── src/
│   └── data_loader.py         # Data loading, validation, and derived columns
├── tests/
│   └── test_data_loader.py   # Unit tests for the data loader
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
notebooks or scripts.