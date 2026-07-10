"""
test_data_loader.py

Unit tests for src/data_loader.py, run against the real
data/raw/BrentOilPrices.csv as well as small synthetic edge cases.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.data_loader import load_brent_prices, volatility_by_period

RAW_DATA_PATH = (
    Path(__file__).resolve().parents[1] / "data" / "raw" / "BrentOilPrices.csv"
)


@pytest.fixture(scope="module")
def brent_df():
    return load_brent_prices(RAW_DATA_PATH, verbose=False)


def test_loads_expected_columns(brent_df):
    expected = {"Date", "Price", "log_price", "log_return"}
    assert expected.issubset(brent_df.columns)


def test_no_missing_dates(brent_df):
    assert brent_df["Date"].isna().sum() == 0


def test_dates_are_sorted(brent_df):
    assert brent_df["Date"].is_monotonic_increasing


def test_date_range_matches_known_bounds(brent_df):
    assert brent_df["Date"].min() == pd.Timestamp("1987-05-20")
    assert brent_df["Date"].max() >= pd.Timestamp("2022-09-30")


def test_log_return_first_row_is_nan(brent_df):
    assert np.isnan(brent_df["log_return"].iloc[0])


def test_log_return_matches_manual_calculation(brent_df):
    # Spot-check row 1 against a manual log-diff computation
    expected = np.log(brent_df["Price"].iloc[1]) - np.log(brent_df["Price"].iloc[0])
    assert np.isclose(brent_df["log_return"].iloc[1], expected)


def test_rejects_non_positive_price(tmp_path):
    bad_csv = tmp_path / "bad_prices.csv"
    bad_csv.write_text("Date,Price\n20-May-87,18.63\n21-May-87,-5.0\n")
    with pytest.raises(ValueError, match="non-positive"):
        load_brent_prices(bad_csv, verbose=False)


def test_rejects_unparseable_date(tmp_path):
    bad_csv = tmp_path / "bad_dates.csv"
    bad_csv.write_text("Date,Price\n2023/13/40,18.63\n21-May-87,18.45\n")
    with pytest.raises(ValueError, match="did not match either known format"):
        load_brent_prices(bad_csv, verbose=False)


def test_missing_required_columns(tmp_path):
    bad_csv = tmp_path / "wrong_columns.csv"
    bad_csv.write_text("Timestamp,Value\n20-May-87,18.63\n")
    with pytest.raises(ValueError, match="Expected columns"):
        load_brent_prices(bad_csv, verbose=False)


def test_volatility_by_period_shape(brent_df):
    result = volatility_by_period(brent_df)
    assert list(result.columns) == ["period", "n_obs", "log_return_std"]
    assert len(result) == 5
    assert result["n_obs"].sum() <= len(brent_df)


def test_volatility_2020_2022_higher_than_2009_2014(brent_df):
    # Known finding from Task 1 EDA: volatility roughly doubled post-2020
    result = volatility_by_period(brent_df).set_index("period")
    calm_period_std = result.loc["2009-2014", "log_return_std"]
    volatile_period_std = result.loc["2020-2022", "log_return_std"]
    assert volatile_period_std > calm_period_std
