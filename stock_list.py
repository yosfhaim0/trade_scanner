import json
from pathlib import Path
from typing import List, Dict

import yfinance as yf

STOCKS_FILE = "stock_list"


def _fetch_tickers() -> List[str]:
    """Gather a broad list of US tickers using yfinance helper functions."""
    if yf is None:
        return []

    tickers = []
    for func_name in [
        "tickers_sp500",
        "tickers_nasdaq",
        "tickers_other",
        "tickers_dow",
        "tickers_ibovespa",  # broad coverage if available
        "tickers_ftse100",
        "tickers_nifty50",
    ]:
        func = getattr(yf, func_name, None)
        if callable(func):
            tickers.extend(func())
    return sorted(set(tickers))


def build_stock_list(path: str = STOCKS_FILE) -> List[Dict]:
    """Fetch metadata for many US stocks and cache to a JSON file."""
    if yf is None:
        raise RuntimeError("yfinance is required to build the stock list")

    tickers = _fetch_tickers()
    stocks: List[Dict] = []
    for t in tickers:
        try:
            ticker = yf.Ticker(t)
            info = ticker.info or {}
            options = bool(getattr(ticker, "options", []))
            stocks.append(
                {
                    "ticker": t,
                    "name": info.get("shortName") or info.get("longName"),
                    "sector": info.get("sector"),
                    "market_cap": info.get("marketCap"),
                    "options": options,
                }
            )
        except Exception:
            # Skip tickers that cause issues
            continue

    with open(path, "w") as f:
        json.dump(stocks, f)
    return stocks


def load_tickers_from_txt(filepath):
    """
    Loads tickers from a .txt file, one per line.

    Args:
        filepath (str): Path to the .txt file

    Returns:
        List[Dict]: A list of ticker symbols
    """
    tickers = []
    with open(filepath, "r") as file:
        for line in file:
            symbol = line.strip()
            if symbol:  # ignore empty lines
                tickers.append({
    "ticker": symbol,
    "sector": "",
    "has_options": True
  })
    return tickers

def load_stock_list(path: str = STOCKS_FILE) -> List[Dict]:
    """Load cached stock list; build it if missing."""
    # p = Path(path)
    # if p.exists():
    #     try:
    #         with p.open() as f:
    #             return json.load(f)
    #     except Exception:
    #         pass
    return load_tickers_from_txt(path)
    # return build_stock_list(path)
