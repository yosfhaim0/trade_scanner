"""Module to scan tickers for potential trading opportunities."""

from __future__ import annotations

from typing import List, Dict
import sys

from database import Database

import pandas as pd
import yfinance as yf

from stock_list import load_stock_list

try:
    import pandas_ta as ta  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    ta = None


DEFAULT_PERIOD = "60d"
DEFAULT_INTERVAL = "1d"
RSI_PERIOD = 14
STOCH_K = 14
STOCH_D = 3
LOOKBACK_SUPPORT = 20
MIN_DB_ROWS = 60


class DataUnavailableError(Exception):
    """Raised when no data could be retrieved for a ticker."""


def _display_progress(current: int, total: int) -> None:
    """Simple progress bar printing percentage of completion."""
    percent = int((current / total) * 100)
    msg = f"Scanning tickers: {current}/{total} ({percent}%)"
    print(f"\r{msg}", end="", file=sys.stdout, flush=True)
    if current == total:
        print(file=sys.stdout)


# Helper functions

def _fetch_from_db(db: Database, ticker: str) -> pd.DataFrame:
    """Load historical data for ``ticker`` from the database."""
    df = db.fetch_ticker(ticker)
    if df.empty:
        return df
    df = df.rename(
        columns={
            "datetime": "Date",
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "volume": "Volume",
        }
    )
    df["Date"] = pd.to_datetime(df["Date"])
    df.set_index("Date", inplace=True)
    return df

def _download(ticker: str) -> pd.DataFrame:
    """Download historical data for a single ticker."""
    print(f"downlaod: {ticker} for DEFAULT_PERIOD:{DEFAULT_PERIOD} interval: {DEFAULT_INTERVAL}")
    df = yf.download(ticker, period=DEFAULT_PERIOD, interval=DEFAULT_INTERVAL, progress=False)
    if df.empty:
        raise DataUnavailableError(f"No data for {ticker}")
    df.index.name = "Date"
    return df


def _get_data(db: Database, ticker) -> pd.DataFrame:
    """Retrieve data from the DB or download if missing."""
    ticker=ticker['ticker']
    df = _fetch_from_db(db, ticker)
    if len(df) >= MIN_DB_ROWS:
        return df

    df = _download(ticker)
    df_to_store = df.reset_index()
    df_to_store["Ticker"] = ticker
    db.insert_dataframe(df_to_store)
    return df


def _add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add RSI and Stochastic indicators."""
    if ta is None:
        raise ImportError("pandas_ta library is required")

    df = df.copy()
    df["RSI"] = ta.rsi(df["Close"], length=RSI_PERIOD)
    df = df[~df.index.duplicated(keep="last")]  # remove duplicated timestamps
    stoch = ta.stoch(df["High"], df["Low"], df["Close"], k=STOCH_K, d=STOCH_D)
    if stoch is None or stoch.empty:
        df["STOCHk"] = pd.NA
        df["STOCHd"] = pd.NA
    else:
        k_col = stoch.columns[0]
        d_col = stoch.columns[1] if len(stoch.columns) > 1 else stoch.columns[0]
        df["STOCHk"] = stoch[k_col]
        df["STOCHd"] = stoch[d_col]

        # Propagate the last valid indicator values forward to avoid ``None`` when
        # there is insufficient data for the final row.
    df[["RSI", "STOCHk", "STOCHd"]] = df[["RSI", "STOCHk", "STOCHd"]].ffill()
    return df


def _support_resistance(df: pd.DataFrame, lookback: int = LOOKBACK_SUPPORT) -> Dict[str, float]:
    recent = df.tail(lookback)
    support = float(recent["Low"].min())
    resistance = float(recent["High"].max())
    return {"support": support, "resistance": resistance}


# Public API

def find_opportunities(
    tickers: List[str],
    mode: str = "both",
    min_volume: int = 0,
    min_price: float = 0.0,
    max_price: float = float("inf"),
    show_progress: bool = False,
) -> List[Dict[str, object]]:
    """Scan tickers for overbought or oversold conditions.

    Parameters
    ----------
    tickers : List[str]
        Symbols to scan.
    mode : str, optional
        'overbought', 'oversold', or 'both'. Defaults to 'both'.
    min_volume : int, optional
        Skip tickers with volume below this value.
    min_price : float, optional
        Skip tickers with a closing price below this value.
    max_price : float, optional
        Skip tickers with a closing price above this value.
    show_progress : bool, optional
        Display a progress indicator while scanning.

    Returns
    -------
    List[Dict[str, object]]
        Each dict contains ticker, RSI, STOCHk, STOCHd, status, support, and
        resistance.
    """
    mode = mode.lower()
    if mode not in {"overbought", "oversold", "both"}:
        raise ValueError("mode must be 'overbought', 'oversold', or 'both'")

    db = Database()
    results: List[Dict[str, object]] = []

    total = len(tickers)
    for idx, ticker in enumerate(tickers, start=1):
        if show_progress:
            _display_progress(idx, total)


        df = _get_data(db, ticker)


        df = _add_indicators(df)
        last_row = df.iloc[-1]

        try:
            volume_val = float(last_row["Volume"])
            price_val = float(last_row["Close"])
        except (KeyError, TypeError, ValueError):
            continue

        if volume_val < min_volume or price_val < min_price or price_val > max_price:
            continue

        indicators = last_row
        try:
            rsi_val = float(indicators["RSI"])
            stoch_k = float(indicators["STOCHk"])
            stoch_d = float(indicators["STOCHd"])
        except (TypeError, ValueError):
            # Skip this ticker if indicators could not be calculated
            continue

        overbought = rsi_val >= 70 and stoch_k >= 80 and stoch_d >= 80
        oversold = rsi_val <= 30 and stoch_k <= 20 and stoch_d <= 20

        status = None
        if overbought:
            status = "overbought"
        elif oversold:
            status = "oversold"

        if status is None:
            continue
        if mode != "both" and status != mode:
            continue

        levels = _support_resistance(df)

        results.append(
            {
                "ticker": ticker,
                "price": price_val,
                "rsi": rsi_val,
                "stoch_k": stoch_k,
                "stoch_d": stoch_d,
                "status": status,
                "support": levels["support"],
                "resistance": levels["resistance"],
            }
        )

    db.close()
    return results


if __name__ == '__main__':
    from tabulate import tabulate

    l = load_stock_list()
    results = find_opportunities(l[:20], show_progress=True)

    if not results:
        print("No opportunities found.")
    else:
        display_table = []
        for row in results:
            icon = "🔼" if row["status"] == "overbought" else "🔽"
            display_table.append([
                row["ticker"]['ticker'],
                f'{row["price"]:.2f}',
                f'{row["rsi"]:.2f}',
                f'{row["stoch_k"]:.2f}',
                f'{row["stoch_d"]:.2f}',
                f'{icon} {row["status"].capitalize()}',
                f'{row["support"]:.2f}',
                f'{row["resistance"]:.2f}',
            ])

        headers = ["Ticker",'Price', "RSI", "Stoch %K", "Stoch %D", "Status", "Support", "Resistance"]
        print(tabulate(display_table, headers=headers, tablefmt="fancy_grid"))
