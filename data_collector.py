import yfinance as yf
from typing import List
import pandas as pd


class DataCollector:
    """Fetches historical and current market data using yfinance."""

    def __init__(self, tickers: List[str]):
        self.tickers = tickers

    def fetch_historical(self, period: str = "30d", interval: str = "1d") -> dict:
        """Download historical OHLCV data for all tickers."""
        data = {}
        for ticker in self.tickers:
            df = yf.download(ticker, period=period, interval=interval, progress=False)
            df.reset_index(inplace=True)
            df["Ticker"] = ticker
            data[ticker] = df
        return data

    def fetch_latest(self) -> pd.DataFrame:
        """Fetch the latest quote for each ticker."""
        frames = []
        for ticker in self.tickers:
            quote = yf.Ticker(ticker).history(period="1d")
            quote.reset_index(inplace=True)
            quote["Ticker"] = ticker
            frames.append(quote.tail(1))
        return pd.concat(frames, ignore_index=True)
