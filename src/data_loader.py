"""
data_loader.py

Loads and cleans the Brent oil price dataset for change point analysis.

Handles:
- Two date formats present in the raw file ('DD-Mon-YY' and 'Mon DD, YYYY')
- Missing value and duplicate-date checks
- Derived columns: log price and log return, used for stationarity-friendly modeling
"""

from pathlib import Path
import numpy as np
import pandas as pd

# Date formats observed in the raw BrentOilPrices.csv file, in the order
# they appear chronologically (format changes around 22-Apr-2020).
_DATE_FORMATS = ("%d-%b-%y", "%b %d, %Y")


def _parse_date(value: str) -> pd.Timestamp:
    """Parse a single date string, trying each known format in turn.

    Returns pd.NaT if none of the known formats match, rather than raising,
    so that malformed rows can be surfaced in bulk during quality checks
    instead of crashing the load.
    """
    for fmt in _DATE_FORMATS:
        try:
            return pd.to_datetime(value, format=fmt)
        except ValueError:
            continue
    return pd.NaT


def load_brent_prices(
    path: str | Path,
    verbose: bool = True,
) -> pd.DataFrame:
    """Load, clean, and enrich the Brent oil price dataset.

    Parameters
    ----------
    path : str or Path
        Path to the raw BrentOilPrices.csv file (columns: Date, Price).
    verbose : bool, default True
        If True, print a short data-quality summary after loading.

    Returns
    -------
    pd.DataFrame
        Cleaned dataframe sorted by date, indexed 0..n-1, with columns:
        - Date       : parsed datetime
        - Price      : float, USD per barrel
        - log_price  : natural log of Price
        - log_return : log(Price_t) - log(Price_{t-1}); first row is NaN

    Raises
    ------
    ValueError
        If any date fails to parse under the known formats (NaT produced),
        or if the Price column contains non-positive values (which would
        break the log transform).
    """
    df = pd.read_csv(path)

    if not {"Date", "Price"}.issubset(df.columns):
        raise ValueError(f"Expected columns 'Date' and 'Price', got {list(df.columns)}")

    df["Date"] = df["Date"].apply(_parse_date)

    n_unparsed = df["Date"].isna().sum()
    if n_unparsed > 0:
        raise ValueError(
            f"{n_unparsed} row(s) had a Date that did not match either known "
            f"format {_DATE_FORMATS}. Inspect these rows before proceeding."
        )

    if (df["Price"] <= 0).any():
        raise ValueError(
            "Price column contains non-positive values; cannot take log()."
        )

    n_duplicates = df["Date"].duplicated().sum()

    df = df.sort_values("Date").reset_index(drop=True)

    df["log_price"] = np.log(df["Price"])
    df["log_return"] = df["log_price"].diff()

    if verbose:
        print("Brent oil price data loaded")
        print(f"  Rows              : {len(df)}")
        print(
            f"  Date range        : {df['Date'].min().date()} to {df['Date'].max().date()}"
        )
        print(f"  Duplicate dates   : {n_duplicates}")
        print(
            f"  Price range (USD) : {df['Price'].min():.2f} - {df['Price'].max():.2f}"
        )

    return df


def volatility_by_period(
    df: pd.DataFrame,
    periods: list[tuple[int, int, str]] | None = None,
) -> pd.DataFrame:
    """Compute log-return standard deviation (volatility) across date ranges.

    Parameters
    ----------
    df : pd.DataFrame
        Output of load_brent_prices (must contain 'Date' and 'log_return').
    periods : list of (start_year, end_year, label), optional
        Inclusive year ranges to summarize. Defaults to a standard
        decade-ish breakdown covering the full 1987-2022 dataset.

    Returns
    -------
    pd.DataFrame
        One row per period with columns: period, n_obs, log_return_std.
    """
    if periods is None:
        periods = [
            (1987, 1999, "1987-1999"),
            (2000, 2008, "2000-2008"),
            (2009, 2014, "2009-2014"),
            (2015, 2019, "2015-2019"),
            (2020, 2022, "2020-2022"),
        ]

    years = df["Date"].dt.year
    rows = []
    for lo, hi, label in periods:
        mask = (years >= lo) & (years <= hi)
        rows.append(
            {
                "period": label,
                "n_obs": int(mask.sum()),
                "log_return_std": df.loc[mask, "log_return"].std(),
            }
        )
    return pd.DataFrame(rows)
