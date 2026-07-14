"""
changepoint_model.py

Bayesian single change-point model for Brent oil prices (Task 2).

Design note: PyMC/ArviZ are imported *inside* the functions that need them,
not at module level. This means the date-conversion and event-matching
helpers below can be imported and unit-tested even in environments where
PyMC isn't installed - useful for CI or quick checks, since PyMC is a heavy
dependency with native-compilation requirements.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def build_single_changepoint_model(values):
    """Build (but do not sample) a single change-point PyMC model.

    Model:
        tau            ~ DiscreteUniform(0, n-1)          # change point index
        mu1, mu2       ~ Normal(mean(values), 2*std(values))
        sigma          ~ HalfNormal(std(values))
        mu(t)          = mu1 if t <= tau else mu2          # pm.math.switch
        values[t]      ~ Normal(mu(t), sigma)

    Parameters
    ----------
    values : array-like
        The series to model (e.g. df['Price'].values). Should not contain
        NaNs - drop/handle those before calling this.

    Returns
    -------
    pymc.Model
        Unsampled model, ready for `sample_model()`.
    """
    import pymc as pm  # local import - keeps this module importable without pymc

    values = np.asarray(values, dtype=float)
    n = len(values)
    idx = np.arange(n)

    with pm.Model() as model:
        tau = pm.DiscreteUniform("tau", lower=0, upper=n - 1)
        mu1 = pm.Normal("mu1", mu=values.mean(), sigma=2 * values.std())
        mu2 = pm.Normal("mu2", mu=values.mean(), sigma=2 * values.std())
        sigma = pm.HalfNormal("sigma", sigma=values.std())

        # tau >= idx is True for all days up to and including the change
        # point -> those days get mu1; everything after gets mu2.
        mu = pm.math.switch(tau >= idx, mu1, mu2)
        pm.Normal("obs", mu=mu, sigma=sigma, observed=values)

    return model


def sample_model(
    model,
    draws: int = 2000,
    tune: int = 1000,
    chains: int = 4,
    target_accept: float = 0.9,
    random_seed: int = 42,
):
    """Run MCMC sampling on a built model and return the InferenceData.

    Parameters mirror pm.sample() defaults recommended for this kind of
    model: 4 chains for reliable r_hat estimates, target_accept raised
    slightly above PyMC's 0.8 default since discrete + continuous mixed
    models can need a bit more care to avoid divergences.
    """
    import pymc as pm

    with model:
        idata = pm.sample(
            draws=draws,
            tune=tune,
            chains=chains,
            target_accept=target_accept,
            random_seed=random_seed,
        )
    return idata


def tau_to_date(tau_value: float, dates) -> pd.Timestamp:
    """Convert a tau index (integer position in the series) to its date.

    Parameters
    ----------
    tau_value : float or int
        A tau value, e.g. the posterior mean/mode, or an HDI bound.
        Rounded and clipped to a valid index.
    dates : array-like of dates (e.g. a pd.Series or DatetimeIndex)
        Must be the same length/order as the series the model was fit on.
    """
    idx = int(round(tau_value))
    idx = max(0, min(idx, len(dates) - 1))
    if hasattr(dates, "iloc"):
        return pd.Timestamp(dates.iloc[idx])
    return pd.Timestamp(dates[idx])


def summarize_changepoint(idata, dates) -> dict:
    """Summarize a fitted single change-point model's posterior.

    Parameters
    ----------
    idata : arviz.InferenceData
        Output of `sample_model()`.
    dates : array-like of dates
        Same length/order as the series the model was fit on.

    Returns
    -------
    dict with:
        tau_mode_date       : most probable change point date
        tau_hdi_dates       : (low, high) dates bounding the 94% HDI on tau
        mu1_mean, mu2_mean  : posterior mean price before/after
        mu1_hdi, mu2_hdi    : (low, high) 94% HDI for each regime mean
        pct_change_mean     : mean % change from regime 1 to regime 2
        pct_change_hdi      : (low, high) 94% HDI on the % change
        rhat_max            : largest r_hat across tau/mu1/mu2/sigma
                              (should be close to 1.0; > 1.01 signals a
                              convergence problem worth investigating)
    """
    import arviz as az

    # The mean-only model has one 'sigma'; the variance-shift model has
    # 'sigma1'/'sigma2' instead. Detect which variables actually exist in
    # this idata rather than hardcoding 'sigma', so this function works
    # for both build_single_changepoint_model and
    # build_changepoint_model_with_variance_shift outputs.
    available = set(idata.posterior.data_vars)
    base_vars = ["tau", "mu1", "mu2"]
    if "sigma" in available:
        sigma_vars = ["sigma"]
    elif {"sigma1", "sigma2"}.issubset(available):
        sigma_vars = ["sigma1", "sigma2"]
    else:
        sigma_vars = []
    var_names = base_vars + sigma_vars

    summary = az.summary(idata, var_names=var_names)
    rhat_max = float(summary["r_hat"].max())

    tau_samples = idata.posterior["tau"].values.flatten()
    tau_mode = int(pd.Series(tau_samples).mode().iloc[0])
    tau_mode_date = tau_to_date(tau_mode, dates)

    tau_hdi = az.hdi(idata, var_names=["tau"])["tau"].values
    tau_hdi_dates = (
        tau_to_date(tau_hdi[0], dates),
        tau_to_date(tau_hdi[1], dates),
    )

    mu1_samples = idata.posterior["mu1"].values.flatten()
    mu2_samples = idata.posterior["mu2"].values.flatten()

    mu1_mean, mu2_mean = float(mu1_samples.mean()), float(mu2_samples.mean())
    mu1_hdi = tuple(az.hdi(idata, var_names=["mu1"])["mu1"].values)
    mu2_hdi = tuple(az.hdi(idata, var_names=["mu2"])["mu2"].values)

    pct_change_samples = (mu2_samples - mu1_samples) / mu1_samples
    pct_change_mean = float(pct_change_samples.mean())
    pct_change_hdi = tuple(np.percentile(pct_change_samples, [3, 97]))

    return {
        "summary_table": summary,
        "rhat_max": rhat_max,
        "tau_mode_date": tau_mode_date,
        "tau_hdi_dates": tau_hdi_dates,
        "mu1_mean": mu1_mean,
        "mu2_mean": mu2_mean,
        "mu1_hdi": mu1_hdi,
        "mu2_hdi": mu2_hdi,
        "pct_change_mean": pct_change_mean,
        "pct_change_hdi": pct_change_hdi,
    }


def match_nearest_event(change_date, events_df: pd.DataFrame, window_days: int = 90):
    """Find the event in events_df closest in time to change_date.

    Only returns a match if an event falls within +/- window_days -
    otherwise returns None, since a distant "closest" event is not a
    meaningful association.

    IMPORTANT: this returns a *temporal* match only. Proximity in time is
    not proof of causation - see the correlation-vs-causation discussion
    in notebooks/README.md before treating a match as a causal finding.

    Parameters
    ----------
    change_date : date-like
        The detected change point date (e.g. tau_mode_date).
    events_df : pd.DataFrame
        Must have a 'date' column (parseable) and 'event_name', 'category',
        'expected_direction', 'description' columns, matching data/events.csv.
    window_days : int, default 90
        Maximum distance (in days, either direction) to count as a match.

    Returns
    -------
    dict or None
        Nearest matching event's details plus day_offset (positive = event
        came after the change point; negative = event came before), or
        None if nothing falls within the window.
    """
    events = events_df.copy()
    events["date"] = pd.to_datetime(events["date"])
    change_date = pd.Timestamp(change_date)

    events["day_offset"] = (events["date"] - change_date).dt.days
    events["abs_offset"] = events["day_offset"].abs()

    within_window = events[events["abs_offset"] <= window_days]
    if within_window.empty:
        return None

    nearest = within_window.sort_values("abs_offset").iloc[0]
    return {
        "event_name": nearest["event_name"],
        "event_date": nearest["date"],
        "day_offset": int(nearest["day_offset"]),
        "category": nearest["category"],
        "expected_direction": nearest["expected_direction"],
        "description": nearest["description"],
    }


def slice_window(
    df: pd.DataFrame,
    center_date,
    years_before: float = 2,
    years_after: float = 2,
) -> pd.DataFrame:
    """Slice a date-indexed dataframe to a window around a suspected event.

    Used for the "targeted rolling window" approach: instead of fitting one
    global change-point model on the full 35-year series (which tends to
    land near the series' temporal midpoint on trending data - see
    notebooks/README.md discussion), fit small, fast, local models each
    centered on a specific known event.

    NOTE ON INTERPRETATION: because the window is centered on a date you
    already suspect is relevant, a change point found here is an estimate
    of that event's *local impact*, not an independent discovery that the
    event mattered. Frame results from this function as confirmatory /
    event-study analysis, not exploratory change-point detection.

    Parameters
    ----------
    df : pd.DataFrame
        Must have a 'Date' column (datetime), e.g. output of load_brent_prices.
    center_date : date-like
        The suspected event date to center the window on.
    years_before, years_after : float, default 2
        How many years of data to include on each side of center_date.

    Returns
    -------
    pd.DataFrame
        The sliced rows, with index reset to 0..len-1 (required so that
        build_single_changepoint_model's day-index-based tau lines up
        with this window's own dates, not the original full-series index).
    """
    center = pd.Timestamp(center_date)
    # pd.DateOffset(years=...) rejects non-integer years (it's built on
    # dateutil.relativedelta, which treats fractional years as ambiguous).
    # Use Timedelta in days instead, so years_before/years_after can be
    # fractional (e.g. 1.5) without raising ValueError.
    start = center - pd.Timedelta(days=years_before * 365.25)
    end = center + pd.Timedelta(days=years_after * 365.25)
    window = df[(df["Date"] >= start) & (df["Date"] <= end)].reset_index(drop=True)
    return window


def build_changepoint_model_with_variance_shift(values):
    """Single change-point model where BOTH mean and variance can shift.

    Extends build_single_changepoint_model() by giving each regime its own
    sigma (sigma1, sigma2) instead of one shared sigma. Motivated directly
    by the Task 1 EDA finding that volatility is not constant over time
    (e.g. roughly doubling in 2020-2022) - the plain mean-shift model can't
    represent that, since it forces one variance across the whole series.

    Model:
        tau                     ~ DiscreteUniform(0, n-1)
        mu1, mu2                ~ Normal(mean(values), 2*std(values))
        sigma1, sigma2          ~ HalfNormal(std(values))
        mu(t)                   = mu1 if t <= tau else mu2
        sigma(t)                = sigma1 if t <= tau else sigma2
        values[t]                ~ Normal(mu(t), sigma(t))

    Best used on a targeted window (via slice_window) around an event
    suspected to change *volatility*, not just the price level - e.g. the
    2020 Saudi-Russia price war / COVID period, or the 2011 Arab Spring.
    """
    import pymc as pm

    values = np.asarray(values, dtype=float)
    n = len(values)
    idx = np.arange(n)

    with pm.Model() as model:
        tau = pm.DiscreteUniform("tau", lower=0, upper=n - 1)
        mu1 = pm.Normal("mu1", mu=values.mean(), sigma=2 * values.std())
        mu2 = pm.Normal("mu2", mu=values.mean(), sigma=2 * values.std())
        sigma1 = pm.HalfNormal("sigma1", sigma=values.std())
        sigma2 = pm.HalfNormal("sigma2", sigma=values.std())

        mu = pm.math.switch(tau >= idx, mu1, mu2)
        sigma = pm.math.switch(tau >= idx, sigma1, sigma2)
        pm.Normal("obs", mu=mu, sigma=sigma, observed=values)

    return model


def run_windowed_changepoint(
    df: pd.DataFrame,
    event_date,
    events_df: pd.DataFrame,
    years_before: float = 1.5,
    years_after: float = 1.5,
    variance_shift: bool = False,
    event_window_days: int = 120,
    draws: int = 1000,
    tune: int = 500,
    chains: int = 4,
    random_seed: int = 42,
) -> dict:
    """Run the full targeted-window pipeline for one suspected event.

    Combines slice_window -> build model -> sample -> summarize -> match
    into a single call, to keep the notebook's per-event loop short.

    Reminder: because the window is centered on a date you already
    suspect is relevant, this is a CONFIRMATORY / event-study analysis of
    a known date, not an independent discovery. Report it as "estimated
    local impact of [event]", not "the model found this on its own."

    Parameters
    ----------
    df : pd.DataFrame
        Full cleaned series (output of load_brent_prices).
    event_date : date-like
        The suspected event date to center the window on.
    events_df : pd.DataFrame
        The events dataset (data/events.csv), used to label the match.
    years_before, years_after : float
        Window size around event_date.
    variance_shift : bool, default False
        If True, use build_changepoint_model_with_variance_shift (mean AND
        variance can shift) instead of the plain mean-shift model.
    event_window_days : int
        Passed to match_nearest_event for the final association check.
    draws, tune, chains, random_seed : sampler settings, smaller defaults
        than the global model since these windows are much shorter series.

    Returns
    -------
    dict with keys: window_df, idata, results (from summarize_changepoint),
    matched_event, variance_shift (bool, echoed back for convenience).
    """
    window_df = slice_window(df, event_date, years_before, years_after)

    if variance_shift:
        model = build_changepoint_model_with_variance_shift(window_df["Price"].values)
    else:
        model = build_single_changepoint_model(window_df["Price"].values)

    idata = sample_model(
        model, draws=draws, tune=tune, chains=chains, random_seed=random_seed
    )
    results = summarize_changepoint(idata, window_df["Date"])
    matched_event = match_nearest_event(
        results["tau_mode_date"], events_df, window_days=event_window_days
    )

    return {
        "window_df": window_df,
        "idata": idata,
        "results": results,
        "matched_event": matched_event,
        "variance_shift": variance_shift,
    }


def diagnose_reliability(
    summary_table: pd.DataFrame,
    ess_threshold: int = 400,
    rhat_threshold: float = 1.01,
) -> tuple[bool, str]:
    """Check a fitted model's summary table against standard MCMC thresholds.

    Parameters
    ----------
    summary_table : pd.DataFrame
        The 'summary_table' entry from summarize_changepoint()'s return
        dict (i.e. az.summary() output) - must have 'r_hat', 'ess_bulk',
        and 'ess_tail' columns.
    ess_threshold : int, default 400
        Minimum effective sample size (bulk and tail) to trust the
        posterior mean/HDI - standard rule of thumb from the ArviZ/Stan
        documentation.
    rhat_threshold : float, default 1.01
        Maximum acceptable r_hat. Values above this mean chains have not
        converged to the same distribution.

    Returns
    -------
    (reliable, note) : (bool, str)
        reliable is True only if all three checks pass. note is "OK" or a
        semicolon-separated list of which checks failed and by how much.
    """
    max_rhat = summary_table["r_hat"].max()
    min_ess_bulk = summary_table["ess_bulk"].min()
    min_ess_tail = summary_table["ess_tail"].min()

    issues = []
    if max_rhat > rhat_threshold:
        issues.append(f"r_hat {max_rhat:.4f} > {rhat_threshold}")
    if min_ess_bulk < ess_threshold:
        issues.append(f"ess_bulk {min_ess_bulk:.0f} < {ess_threshold}")
    if min_ess_tail < ess_threshold:
        issues.append(f"ess_tail {min_ess_tail:.0f} < {ess_threshold}")

    reliable = len(issues) == 0
    return reliable, ("OK" if reliable else "; ".join(issues))


def diagnose_all(windowed_results: dict, **kwargs) -> pd.DataFrame:
    """Run diagnose_reliability() across every event in windowed_results.

    Parameters
    ----------
    windowed_results : dict
        {event_name: output_of_run_windowed_changepoint, ...}
    **kwargs
        Passed through to diagnose_reliability (ess_threshold, rhat_threshold).

    Returns
    -------
    pd.DataFrame with columns: Event, Reliable, Issue
    """
    rows = []
    for event_name, out in windowed_results.items():
        reliable, note = diagnose_reliability(out["results"]["summary_table"], **kwargs)
        rows.append({"Event": event_name, "Reliable": reliable, "Issue": note})
    return pd.DataFrame(rows)


def resample_unreliable(
    df: pd.DataFrame,
    windowed_results: dict,
    diagnostics_df: pd.DataFrame,
    events_df: pd.DataFrame,
    target_events: list,
    draws: int = 4000,
    tune: int = 2000,
    chains: int = 4,
    random_seed: int = 42,
) -> list[dict]:
    """Resample every event flagged unreliable, with more draws/tuning.

    Mutates windowed_results in place (replacing entries for any
    unreliable event with a freshly resampled result), and returns a
    report of what was resampled and whether it passed the second time.

    Parameters
    ----------
    df : pd.DataFrame
        Full cleaned series.
    windowed_results : dict
        {event_name: output_of_run_windowed_changepoint, ...} - mutated
        in place for any event that gets resampled.
    diagnostics_df : pd.DataFrame
        Output of diagnose_all(windowed_results) - used to find which
        events need resampling.
    events_df : pd.DataFrame
        The events dataset (data/events.csv).
    target_events : list of (date, name) tuples
        Same list used to build the original windowed_results, needed to
        look up each unreliable event's date.
    draws, tune, chains, random_seed : sampler settings for the re-run.

    Returns
    -------
    list of dicts, one per resampled event: {event_name, reliable, note}
    """
    event_date_lookup = {name: date for date, name in target_events}
    unreliable_events = diagnostics_df.loc[~diagnostics_df["Reliable"], "Event"].tolist()

    report = []
    for event_name in unreliable_events:
        event_date = event_date_lookup[event_name]
        out = run_windowed_changepoint(
            df, event_date, events_df,
            years_before=1.5, years_after=1.5,
            draws=draws, tune=tune, chains=chains, random_seed=random_seed,
        )
        windowed_results[event_name] = out
        reliable, note = diagnose_reliability(out["results"]["summary_table"])
        report.append({"event_name": event_name, "reliable": reliable, "note": note})

    return report


def check_window_stability(
    df: pd.DataFrame,
    event_date,
    events_df: pd.DataFrame,
    window_sizes: list,
    stability_threshold_days: int = 14,
    **sample_kwargs,
) -> dict:
    """Check whether a detected change point is stable across window sizes.

    Convergence diagnostics (diagnose_reliability) confirm the sampler
    explored the posterior properly - they say nothing about whether the
    window boundaries themselves were a good choice. If a change point
    reflects something real about an event, it should land at roughly the
    same date regardless of exactly how wide a window is drawn around it.
    A result that moves a lot as the window changes is more likely an
    artifact of the window's edges than a genuine feature of the data.

    Parameters
    ----------
    df : pd.DataFrame
        Full cleaned series.
    event_date : date-like
        The suspected event date to center each window on.
    events_df : pd.DataFrame
        The events dataset.
    window_sizes : list of float
        Years before/after to try (symmetric each time), e.g. [1.0, 1.5, 2.0].
    stability_threshold_days : int, default 14
        Maximum spread between the smallest and largest detected date,
        across all window sizes, to call the result "stable".
    **sample_kwargs
        Passed through to run_windowed_changepoint (draws, tune, chains,
        random_seed).

    Returns
    -------
    dict with: detected_dates (list of pd.Timestamp, one per window size),
    spread_days (int), stable (bool).
    """
    detected_dates = []
    for years in window_sizes:
        out = run_windowed_changepoint(
            df, event_date, events_df,
            years_before=years, years_after=years,
            **sample_kwargs,
        )
        detected_dates.append(out["results"]["tau_mode_date"])

    spread_days = (max(detected_dates) - min(detected_dates)).days
    stable = spread_days <= stability_threshold_days

    return {
        "detected_dates": detected_dates,
        "spread_days": spread_days,
        "stable": stable,
    }


def build_event_summary_table(windowed_results: dict, target_events: list) -> pd.DataFrame:
    """Build a comparison table across all windowed event results.

    Parameters
    ----------
    windowed_results : dict
        {event_name: output_of_run_windowed_changepoint, ...}
    target_events : list of (date, name) tuples
        The same list used to generate windowed_results, giving each
        event's real/expected date to compare the detected date against.

    Returns
    -------
    pd.DataFrame, sorted by absolute % change (largest impact first), with
    columns: Event, Actual Date, Detected Date, Offset (days),
    Price Before ($), Price After ($), % Change, Max r_hat.
    """
    event_date_lookup = {name: date for date, name in target_events}

    rows = []
    for event_name, out in windowed_results.items():
        r = out["results"]
        actual_date = pd.Timestamp(event_date_lookup[event_name])
        detected_date = r["tau_mode_date"]
        offset_days = (detected_date - actual_date).days
        rows.append({
            "Event": event_name,
            "Actual Date": actual_date.date(),
            "Detected Date": detected_date.date(),
            "Offset (days)": offset_days,
            "Price Before ($)": round(r["mu1_mean"], 2),
            "Price After ($)": round(r["mu2_mean"], 2),
            "% Change": round(r["pct_change_mean"] * 100, 1),
            "Max r_hat": round(r["rhat_max"], 4),
        })

    return (
        pd.DataFrame(rows)
        .sort_values("% Change", key=abs, ascending=False)
        .reset_index(drop=True)
    )


def direction_word(pct: float) -> str:
    """Return 'increase' or 'decrease' for a signed percent-change value."""
    return "increase" if pct > 0 else "decrease"


def generate_impact_statements(summary_df: pd.DataFrame) -> list[str]:
    """Generate the brief's required quantitative-impact sentences.

    One sentence per row of summary_df (output of build_event_summary_table),
    in the format: "Following [event] around [date], the model detects a
    change point on [date], with the average daily price shifting from $X
    to $Y, a Z% [increase/decrease]."
    """
    statements = []
    for _, row in summary_df.iterrows():
        statements.append(
            f"Following {row['Event']} around {row['Actual Date']}, the model detects a "
            f"change point on {row['Detected Date']}, with the average daily price shifting "
            f"from ${row['Price Before ($)']} to ${row['Price After ($)']}, "
            f"a {abs(row['% Change'])}% {direction_word(row['% Change'])}."
        )
    return statements


def export_results_for_dashboard(
    df: pd.DataFrame,
    global_results: dict,
    windowed_results: dict,
    summary_df: pd.DataFrame,
    events_df: pd.DataFrame,
    output_dir: str = "../data/processed",
) -> None:
    """Write everything the Task 3 Flask backend needs as static files.

    This is the hand-off point between Task 2 (notebook, requires PyMC)
    and Task 3 (backend, should NOT require PyMC - it just serves
    pre-computed results). Run this once at the end of the change point
    notebook; the Flask app then only ever reads these files.

    Writes:
        {output_dir}/prices.csv               - Date, Price, log_return
        {output_dir}/global_changepoint.json   - global model result
        {output_dir}/event_changepoints.json   - per-event windowed results
        {output_dir}/events.json               - the events dataset
        {output_dir}/volatility.json           - log-return std dev by period

    Parameters
    ----------
    df : pd.DataFrame
        Full cleaned series (output of load_brent_prices).
    global_results : dict
        Output of summarize_changepoint() for the global model.
    windowed_results : dict
        {event_name: output_of_run_windowed_changepoint, ...}
    summary_df : pd.DataFrame
        Output of build_event_summary_table().
    events_df : pd.DataFrame
        The events dataset (data/events.csv).
    output_dir : str, default "../data/processed"
        Directory to write into (created if it doesn't exist). Default
        assumes this is called from a notebook in notebooks/.
    """
    import json
    from pathlib import Path

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # 1. Historical prices - what the frontend charts against
    df[["Date", "Price", "log_return"]].to_csv(out / "prices.csv", index=False)

    # 2. Global change point result
    global_export = {
        "tau_mode_date": global_results["tau_mode_date"].isoformat(),
        "tau_hdi_dates": [d.isoformat() for d in global_results["tau_hdi_dates"]],
        "mu1_mean": global_results["mu1_mean"],
        "mu2_mean": global_results["mu2_mean"],
        "mu1_hdi": list(global_results["mu1_hdi"]),
        "mu2_hdi": list(global_results["mu2_hdi"]),
        "pct_change_mean": global_results["pct_change_mean"],
        "rhat_max": global_results["rhat_max"],
    }
    with open(out / "global_changepoint.json", "w") as f:
        json.dump(global_export, f, indent=2)

    # 3. Per-event windowed results, in the same shape the summary table
    #    and statements were built from - matched against summary_df so
    #    the JSON includes the (possibly resampled) final numbers.
    event_export = []
    for _, row in summary_df.iterrows():
        event_name = row["Event"]
        matched = windowed_results[event_name]["matched_event"]
        event_export.append({
            "event_name": event_name,
            "actual_date": str(row["Actual Date"]),
            "detected_date": str(row["Detected Date"]),
            "offset_days": int(row["Offset (days)"]),
            "price_before": row["Price Before ($)"],
            "price_after": row["Price After ($)"],
            "pct_change": row["% Change"],
            "rhat_max": row["Max r_hat"],
            "matched_event": matched["event_name"] if matched else None,
        })
    with open(out / "event_changepoints.json", "w") as f:
        json.dump(event_export, f, indent=2)

    # 4. Events dataset, as JSON (frontend likely wants this format, not CSV)
    events_export = events_df.copy()
    events_export["date"] = pd.to_datetime(events_export["date"]).dt.strftime("%Y-%m-%d")
    events_export.to_json(out / "events.json", orient="records", indent=2)

    # 5. Volatility-by-period, and the reliability status of each windowed
    #    event - this is the "performance metrics" data the dashboard
    #    needs for its "key indicators: volatility, average price changes"
    #    feature, which wasn't exposed by any of the files above.
    from .data_loader import volatility_by_period
    vol_table = volatility_by_period(df)
    vol_export = vol_table.to_dict(orient="records")
    for record in vol_export:
        for key, value in record.items():
            if isinstance(value, float) and pd.isna(value):
                record[key] = None
    with open(out / "volatility.json", "w") as f:
        json.dump(vol_export, f, indent=2)

    print(f"Exported dashboard data to {out.resolve()}")
    print(f"  prices.csv:              {len(df)} rows")
    print(f"  global_changepoint.json: 1 result")
    print(f"  event_changepoints.json: {len(event_export)} events")
    print(f"  events.json:             {len(events_export)} events")
    print(f"  volatility.json:         {len(vol_export)} periods")
