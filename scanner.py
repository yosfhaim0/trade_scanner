from typing import List, Optional, Dict

from data_collector import DataCollector
from database import Database
from analyzer import add_indicators, support_resistance
from stock_list import load_stock_list
from filters import filter_by_sector, filter_options_only


class Scanner:
    """Runs the overall scanning logic with optional filtering."""

    def __init__(self, tickers: Optional[List[str]] = None):
        self.tickers = tickers or []
        self.db = Database()

    def update_data(self, tickers: List[str]):
        """Fetch and store fresh historical data for given tickers."""
        collector = DataCollector(tickers)
        data = collector.fetch_historical()
        for df in data.values():
            self.db.insert_dataframe(df)

    def _select_tickers(
        self,
        sector: Optional[str] = None,
        options_only: bool = False,
        limit: Optional[int] = None,
    ) -> List[str]:
        stocks = load_stock_list()
        if self.tickers:
            stocks = [s for s in stocks if s["ticker"] in self.tickers]
        if sector:
            stocks = filter_by_sector(stocks, sector)
        if options_only:
            stocks = filter_options_only(stocks)
        if limit:
            stocks = stocks[:limit]
        return [s["ticker"] for s in stocks]

    def scan(
        self,
        sector: Optional[str] = None,
        options_only: bool = False,
        limit: Optional[int] = None,
    ) -> List[Dict]:
        """Analyze selected tickers and return trading signals."""
        tickers = self._select_tickers(sector, options_only, limit)
        if not tickers:
            return []

        self.update_data(tickers)

        results = []
        for ticker in tickers:
            df = self.db.fetch_ticker(ticker)
            if df.empty:
                continue
            df = add_indicators(df)
            levels = support_resistance(df)
            last = df.iloc[-1]
            price = last["close"]
            if levels["support"] == 0 and levels["resistance"] == 0:
                continue
            near_support = abs(price - levels["support"]) / price < 0.02
            near_resistance = abs(price - levels["resistance"]) / price < 0.02
            if (
                last["RSI14"] > 70
                or last["RSI14"] < 30
                or near_support
                or near_resistance
            ):
                results.append(
                    {
                        "ticker": ticker,
                        "price": price,
                        "RSI14": last["RSI14"],
                        "support": levels["support"],
                        "resistance": levels["resistance"],
                        "near_support": near_support,
                        "near_resistance": near_resistance,
                    }
                )
        return results

    def close(self):
        self.db.close()
