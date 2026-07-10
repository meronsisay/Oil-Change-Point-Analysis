"""
test_data_loader.py

Unit tests for src/data_loader.py.

Sample data is embedded directly in this file (SAMPLE_CSV below) and
written to a pytest tmp_path at test time. This avoids depending on the
real data/raw/BrentOilPrices.csv, which is intentionally gitignored and
not available in CI, and avoids needing a separate committed fixture file.
"""

import numpy as np
import pandas as pd
import pytest

from src.data_loader import load_brent_prices, volatility_by_period

# 15 rows covering both date formats found in the real dataset:
# 'DD-Mon-YY' (used through Apr 2020) and 'Mon DD, YYYY' (used after,
# quoted here because the date itself contains a comma).
SAMPLE_CSV = """Date,Price
20-May-87,18.63
21-May-87,18.45
22-May-87,18.55
25-May-87,18.60
26-May-87,18.63
15-Jun-09,68.20
16-Jun-09,70.10
17-Jun-09,69.55
01-Mar-20,45.30
02-Mar-20,44.10
"Apr 22, 2020",13.77
"Apr 23, 2020",15.06
"Apr 24, 2020",15.87
"Jan 03, 2022",79.80
"Jan 04, 2022",81.20
"""


@pytest.fixture
def brent_df(tmp_path):
    csv_path = tmp_path / "sample_brent_prices.csv"
    csv_path.write_text(SAMPLE_CSV)
    return load_brent_prices(csv_path, verbose=False)


def test_loads_expected_columns(brent_df):
    expected = {"Date", "Price", "log_price", "log_return"}
    assert expected.issubset(brent_df.columns)


def test_no_missing_dates(brent_df):
    assert brent_df["Date"].isna().sum() == 0


def test_dates_are_sorted(brent_df):
    assert brent_df["Date"].is_monotonic_increasing


def test_both_date_formats_parsed(brent_df):
    assert brent_df["Date"].min() == pd.Timestamp("1987-05-20")
    assert brent_df["Date"].max() == pd.Timestamp("2022-01-04")
    assert len(brent_df) == 15


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