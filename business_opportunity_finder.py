"""Module to scan tickers for potential trading opportunities."""

from __future__ import annotations

from typing import List, Dict

import pandas as pd
import yfinance as yf

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


class DataUnavailableError(Exception):
    """Raised when no data could be retrieved for a ticker."""


# Helper functions

def _download(ticker: str) -> pd.DataFrame:
    """Download historical data for a single ticker."""
    df = yf.download(ticker, period=DEFAULT_PERIOD, interval=DEFAULT_INTERVAL, progress=False)
    if df.empty:
        raise DataUnavailableError(f"No data for {ticker}")
    df.index.name = "Date"
    return df


def _add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add RSI and Stochastic indicators."""
    if ta is None:
        raise ImportError("pandas_ta library is required")

    df = df.copy()
    df["RSI"] = ta.rsi(df["Close"], length=RSI_PERIOD)
    stoch = ta.stoch(df["High"], df["Low"], df["Close"], k=STOCH_K, d=STOCH_D)
    df["STOCHk"] = stoch[f"STOCHk_{STOCH_K}_{STOCH_D}_{STOCH_D}"]
    df["STOCHd"] = stoch[f"STOCHd_{STOCH_K}_{STOCH_D}_{STOCH_D}"]
    return df


def _support_resistance(df: pd.DataFrame, lookback: int = LOOKBACK_SUPPORT) -> Dict[str, float]:
    recent = df.tail(lookback)
    support = float(recent["Low"].min())
    resistance = float(recent["High"].max())
    return {"support": support, "resistance": resistance}


# Public API

def find_opportunities(tickers: List[str], mode: str = "both") -> List[Dict[str, object]]:
    """Scan tickers for overbought or oversold conditions.

    Parameters
    ----------
    tickers : List[str]
        Symbols to scan.
    mode : str, optional
        'overbought', 'oversold', or 'both'. Defaults to 'both'.

    Returns
    -------
    List[Dict[str, object]]
        Each dict contains ticker, RSI, STOCHk, STOCHd, status, support, and
        resistance.
    """
    mode = mode.lower()
    if mode not in {"overbought", "oversold", "both"}:
        raise ValueError("mode must be 'overbought', 'oversold', or 'both'")

    results: List[Dict[str, object]] = []

    for ticker in tickers:
        try:
            df = _download(ticker)
        except DataUnavailableError:
            continue

        df = _add_indicators(df)
        indicators = df.iloc[-1]
        rsi_val = float(indicators["RSI"])
        stoch_k = float(indicators["STOCHk"])
        stoch_d = float(indicators["STOCHd"])

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
                "rsi": rsi_val,
                "stoch_k": stoch_k,
                "stoch_d": stoch_d,
                "status": status,
                "support": levels["support"],
                "resistance": levels["resistance"],
            }
        )

    return results

