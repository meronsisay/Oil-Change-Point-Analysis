# Analysis Workflow — Change Point Analysis of Brent Oil Prices

**Birhan Energies | Data Science Team**

## 1. Data Analysis Workflow

The analysis follows five stages, from raw data to stakeholder-ready insight:

1. **Data loading & cleaning.** Load `BrentOilPrices.csv`, parse `Date` into a
   proper datetime index, sort chronologically, and check for missing values,
   duplicate dates, and format inconsistencies (see Section 4 — the raw file
   mixes two date formats).
2. **Exploratory data analysis (EDA).** Plot the raw price series to spot
   visible trends and shocks; compute and plot log returns
   `log(P_t) - log(P_{t-1})` to assess stationarity and volatility clustering.
3. **Event research.** Compile a structured list of major geopolitical,
   economic, and OPEC-policy events that plausibly moved oil prices
   (`data/events.csv`), to be cross-referenced against detected change
   points later.
4. **Bayesian change point modeling.** Build a PyMC model with a discrete
   uniform prior on the switch point `tau`, two regime means `mu_1`/`mu_2`
   (or on log returns, for volatility regimes), and a `pm.math.switch`
   function feeding a `pm.Normal` likelihood. Sample the posterior with
   `pm.sample()` and check convergence (`r_hat`, trace plots).
5. **Interpretation & reporting.** Identify the posterior mode of `tau`,
   quantify the shift in mean/volatility across the change point, match the
   date against the events list, and communicate findings to stakeholders
   (Section 5).

## 2. Time Series Properties of the Data

Before modeling, the raw dataset was checked directly:

| Property | Finding | Modeling implication |
|---|---|---|
| **Coverage** | 9,011 daily observations, **20-May-1987 to 14-Nov-2022** (no gaps in trading days beyond weekends/holidays; no missing values or duplicate dates) | Note: this extends ~6 weeks beyond the 30-Sep-2022 end date stated in the challenge brief — flagged as a data assumption (Section 6). |
| **Trend** | Price ranges from **$9.10 to $143.95**, with clear multi-year upward and downward regimes rather than a single linear trend (e.g. the 1990s low band, the 2003–2008 run-up to $147, the 2014–2016 collapse) | A single global trend line is a poor model. This is exactly the setting change point models are for — regime-specific means rather than one trend. |
| **Stationarity** | A Dickey-Fuller-style unit-root regression on the raw **price level** gives a coefficient not significantly different from a unit root (t ≈ -1.6, above the ~-2.86 5% critical value) — consistent with a **non-stationary** series. The same regression on **log returns** gives t ≈ -96, far below critical values — log returns are strongly **stationary**. | Model regime *means* on the price level (or log-price) for the core change point task, but use **log returns** for any volatility/variance-regime analysis, since only the return series meets the stationarity assumption most change point/likelihood specifications rely on. |
| **Volatility** | Daily log-return standard deviation is **not constant over time**: ~0.023 in 1987–1999, ~0.024 in 2000–2008, dropping to ~0.019 in 2009–2014, back to ~0.023 in 2015–2019, and spiking to **~0.047** in 2020–2022 (roughly double the historical norm) | Confirms **volatility clustering** — periods of calm and turbulence cluster together. This motivates an extension beyond a single mean-shift model: a change point (or regime-switching) model on variance, not just mean, particularly to capture the 2020 COVID/price-war period. |

## 3. Purpose of Change Point Models

A change point model doesn't assume the data-generating process is constant
across the whole series. Instead, it treats the location of one or more
**structural breaks** — points where the underlying parameters (mean,
variance) shift — as unknown quantities to be estimated from the data itself.

For Brent prices this matters because the series is punctuated by discrete
shocks (wars, OPEC decisions, pandemics) rather than following one smooth
process. A change point model lets the data indicate *when* the regime
shifted and *by how much*, rather than the analyst assuming a break date in
advance. In a Bayesian formulation, this also naturally produces a
**probability distribution** over the break date (`tau`), rather than a
single point estimate — capturing how confident the model is about exactly
when the shift occurred.

## 4. Expected Outputs and Limitations of Change Point Analysis

**Expected outputs:**
- A posterior distribution over the change point date (`tau`); a narrow,
  sharply peaked posterior indicates high confidence in a specific date,
  while a flat/wide posterior indicates the model cannot pin down the break.
- Posterior distributions for the "before" and "after" parameters (e.g.
  `mu_1`, `mu_2`), enabling probabilistic statements such as "there is a
  95% probability the mean price increased by at least $X after `tau`."
- Convergence diagnostics (`r_hat` ≈ 1.0, healthy trace plots) confirming
  the sampler adequately explored the posterior.

**Limitations:**
- The model detects *that* a statistical shift occurred and *when* — it has
  no mechanism for explaining *why*. Any link to a real-world event is a
  hypothesis formed by the analyst after the fact, not something the model
  proves.
- A simple single-change-point model assumes exactly one break; if the
  series contains multiple regime shifts (highly likely over 35 years), the
  model will average across nearby breaks and understate the number and
  precision of actual shifts unless extended to multiple change points.
- Reverse-causality and confounding are not addressed: overlapping events
  (e.g. an OPEC decision announced during a pre-existing demand shock) can't
  be disentangled by a single-variable time series model alone.

## 5. Communication Channels

Given the stakeholder mix identified in the brief — investors, policymakers,
and energy companies, plus a specific mandate to report to government
bodies — outputs will be communicated through:
- A **written analytical report** (PDF/Word) with quantified findings,
  suitable for policymaker and government audiences requiring a formal
  record.
- An **interactive dashboard** (Task 3: Flask + React) allowing investors
  and energy-company analysts to explore price history, change points, and
  event correlations themselves, with filtering and drill-down.
- A concise **executive summary / slide-style briefing** for time-constrained
  stakeholders, highlighting the 2–3 highest-impact change points and their
  quantified price effects.

## 6. Assumptions and Limitations

**Data assumptions:**
- The raw CSV mixes two date formats (`DD-Mon-YY` through 21-Apr-2020, then
  `Mon DD, YYYY` from 22-Apr-2020 onward) — both are parsed explicitly rather
  than relying on automatic inference, to avoid silent misparsing.
- The dataset extends to 14-Nov-2022, roughly six weeks past the 30-Sep-2022
  cutoff mentioned in the brief; the full available range is used unless a
  hard cutoff is specifically required.
- Daily closing prices are assumed accurate as provided, with no adjustment
  for data-source revisions or benchmark changes over the 35-year window.
- Prices are analyzed as quoted (nominal USD/barrel), **not** inflation-adjusted.
  A $100 price in 1990 and in 2022 are not economically equivalent; this is
  noted as a limitation rather than corrected for, unless a real-terms
  analysis is specifically requested.

**Modeling assumptions:**
- A single change point model is the mandatory baseline (per Task 2); it is
  known in advance to be a simplification given the data spans multiple
  well-documented regimes (Section 2). Multiple-change-point or
  regime-switching extensions are noted as future work.
- Regime means are modeled as approximately constant within each detected
  segment; this is a simplification of what are, in reality, continuously
  evolving market conditions.

**Correlation vs. causation — the central limitation:**
A change point detected on or near an event date shows **temporal
association**, not **causal proof**. Establishing causality would require
ruling out confounders, demonstrating a plausible mechanism, and ideally
some form of counterfactual (what would price have done absent the event) —
none of which a univariate change point model on price alone can provide.
Three specific risks apply here:
1. **Event clustering** — major shocks often overlap in time (e.g. Iranian
   sanctions escalating during other OPEC supply discussions), making it
   hard to attribute a detected shift to a single cause.
2. **Reverse causality** — for OPEC decisions in particular, the policy
   itself is often a *response* to already-moving prices, not purely an
   independent shock.
3. **Confounding trends** — macroeconomic conditions (global GDP growth,
   USD strength, inflation) move oil prices independently of the discrete
   events being tracked, and are not controlled for in the baseline model.

Throughout the analysis, detected change points will be described as
**consistent with** or **coincident with** specific events, and explicitly
framed as **hypotheses**, not established causal claims.