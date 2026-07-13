"""
test_changepoint_model.py

Tests only the functions in src/changepoint_model.py that don't require
PyMC/ArviZ - PyMC needs native compilation and isn't installed in CI, so
build_single_changepoint_model, sample_model, summarize_changepoint,
build_changepoint_model_with_variance_shift, run_windowed_changepoint,
resample_unreliable, and check_window_stability are intentionally NOT
tested here. Those are exercised manually by running the notebook, where
PyMC is available.

Covered here: tau_to_date, match_nearest_event, slice_window,
diagnose_reliability, diagnose_all, build_event_summary_table,
direction_word, generate_impact_statements.
"""

import pandas as pd
import pytest

from src.changepoint_model import (
    tau_to_date,
    match_nearest_event,
    slice_window,
    diagnose_reliability,
    diagnose_all,
    build_event_summary_table,
    direction_word,
    generate_impact_statements,
)

# ---------------------------------------------------------------------------
# Shared inline sample data
# ---------------------------------------------------------------------------

SAMPLE_DATES = pd.Series(pd.date_range("2020-01-01", periods=10, freq="D"))

SAMPLE_EVENTS = pd.DataFrame(
    [
        {
            "event_name": "OPEC Declines to Cut Production",
            "date": "2014-11-27",
            "category": "OPEC Policy",
            "expected_direction": "Decrease",
            "description": "OPEC maintains output despite oversupply.",
        },
        {
            "event_name": "Saudi-Russia Oil Price War Begins",
            "date": "2020-03-08",
            "category": "OPEC Policy",
            "expected_direction": "Decrease",
            "description": "Price war triggers steep drop.",
        },
    ]
)

TARGET_EVENTS = [
    ("2014-11-27", "OPEC Declines to Cut Production"),
    ("2020-03-08", "Saudi-Russia Oil Price War Begins"),
]


# ---------------------------------------------------------------------------
# tau_to_date
# ---------------------------------------------------------------------------

def test_tau_to_date_basic():
    assert tau_to_date(5, SAMPLE_DATES) == pd.Timestamp("2020-01-06")


def test_tau_to_date_clips_out_of_range():
    assert tau_to_date(-5, SAMPLE_DATES) == SAMPLE_DATES.iloc[0]
    assert tau_to_date(999, SAMPLE_DATES) == SAMPLE_DATES.iloc[-1]


# ---------------------------------------------------------------------------
# match_nearest_event
# ---------------------------------------------------------------------------

def test_match_nearest_event_exact_date():
    result = match_nearest_event("2020-03-08", SAMPLE_EVENTS, window_days=90)
    assert result is not None
    assert result["event_name"] == "Saudi-Russia Oil Price War Begins"
    assert result["day_offset"] == 0


def test_match_nearest_event_outside_window_returns_none():
    result = match_nearest_event("2010-01-01", SAMPLE_EVENTS, window_days=90)
    assert result is None


# ---------------------------------------------------------------------------
# slice_window
# ---------------------------------------------------------------------------

def test_slice_window_basic_range():
    df = pd.DataFrame({"Date": pd.date_range("2010-01-01", "2020-01-01", freq="D")})
    window = slice_window(df, "2014-11-27", years_before=1, years_after=1)
    assert window["Date"].min() >= pd.Timestamp("2013-11-27")
    assert window["Date"].max() <= pd.Timestamp("2015-11-27")
    assert window.index[0] == 0  # index reset


def test_slice_window_accepts_fractional_years():
    # Regression test: pd.DateOffset(years=1.5) raises ValueError -
    # slice_window must use Timedelta instead so fractional years work.
    df = pd.DataFrame({"Date": pd.date_range("2010-01-01", "2020-01-01", freq="D")})
    window = slice_window(df, "2014-11-27", years_before=1.5, years_after=1.5)
    assert len(window) > 0


# ---------------------------------------------------------------------------
# diagnose_reliability / diagnose_all
# ---------------------------------------------------------------------------

def test_diagnose_reliability_passes_clean_summary():
    good = pd.DataFrame({
        "r_hat": [1.00, 1.00],
        "ess_bulk": [9000.0, 8000.0],
        "ess_tail": [6000.0, 5000.0],
    })
    reliable, note = diagnose_reliability(good)
    assert reliable is True
    assert note == "OK"


def test_diagnose_reliability_flags_high_rhat():
    bad = pd.DataFrame({
        "r_hat": [1.02, 1.00],
        "ess_bulk": [9000.0, 8000.0],
        "ess_tail": [6000.0, 5000.0],
    })
    reliable, note = diagnose_reliability(bad)
    assert reliable is False
    assert "r_hat" in note


def test_diagnose_reliability_flags_low_ess():
    bad = pd.DataFrame({
        "r_hat": [1.00, 1.00],
        "ess_bulk": [150.0, 8000.0],
        "ess_tail": [6000.0, 5000.0],
    })
    reliable, note = diagnose_reliability(bad)
    assert reliable is False
    assert "ess_bulk" in note


def test_diagnose_all_across_multiple_events():
    good = pd.DataFrame({"r_hat": [1.00], "ess_bulk": [9000.0], "ess_tail": [6000.0]})
    bad = pd.DataFrame({"r_hat": [1.02], "ess_bulk": [150.0], "ess_tail": [100.0]})
    windowed_results = {
        "Event A": {"results": {"summary_table": good}},
        "Event B": {"results": {"summary_table": bad}},
    }
    diagnostics_df = diagnose_all(windowed_results)
    assert set(diagnostics_df.columns) == {"Event", "Reliable", "Issue"}
    assert diagnostics_df.loc[diagnostics_df["Event"] == "Event A", "Reliable"].iloc[0] == True
    assert diagnostics_df.loc[diagnostics_df["Event"] == "Event B", "Reliable"].iloc[0] == False


# ---------------------------------------------------------------------------
# build_event_summary_table / direction_word / generate_impact_statements
# ---------------------------------------------------------------------------

MOCK_WINDOWED_RESULTS = {
    "OPEC Declines to Cut Production": {
        "results": {
            "tau_mode_date": pd.Timestamp("2014-11-26"),
            "mu1_mean": 105.09,
            "mu2_mean": 49.17,
            "pct_change_mean": -0.532,
            "rhat_max": 1.02,
        }
    },
    "Saudi-Russia Oil Price War Begins": {
        "results": {
            "tau_mode_date": pd.Timestamp("2020-01-29"),
            "mu1_mean": 65.74,
            "mu2_mean": 51.52,
            "pct_change_mean": -0.216,
            "rhat_max": 1.01,
        }
    },
}


def test_build_event_summary_table_shape_and_sort_order():
    summary_df = build_event_summary_table(MOCK_WINDOWED_RESULTS, TARGET_EVENTS)
    expected_cols = {
        "Event", "Actual Date", "Detected Date", "Offset (days)",
        "Price Before ($)", "Price After ($)", "% Change", "Max r_hat",
    }
    assert set(summary_df.columns) == expected_cols
    assert len(summary_df) == 2
    # Sorted by largest absolute % change first
    assert summary_df.iloc[0]["Event"] == "OPEC Declines to Cut Production"


def test_build_event_summary_table_offset_calculation():
    summary_df = build_event_summary_table(MOCK_WINDOWED_RESULTS, TARGET_EVENTS)
    opec_row = summary_df[summary_df["Event"] == "OPEC Declines to Cut Production"].iloc[0]
    assert opec_row["Offset (days)"] == -1  # detected 1 day before the real date


def test_direction_word():
    assert direction_word(28.1) == "increase"
    assert direction_word(-21.6) == "decrease"


def test_generate_impact_statements_format():
    summary_df = build_event_summary_table(MOCK_WINDOWED_RESULTS, TARGET_EVENTS)
    statements = generate_impact_statements(summary_df)
    assert len(statements) == 2
    assert "53.2% decrease" in statements[0]
    assert "$105.09 to $49.17" in statements[0]