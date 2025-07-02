from typing import List

from data_collector import DataCollector
from database import Database
from analyzer import add_indicators, support_resistance


class Scanner:
    """Runs the overall scanning logic."""

    def __init__(self, tickers: List[str]):
        self.tickers = tickers
        self.collector = DataCollector(tickers)
        self.db = Database()

    def update_data(self):
        """Fetch and store fresh historical data."""
        data = self.collector.fetch_historical()
        for df in data.values():
            self.db.insert_dataframe(df)

    def scan(self):
        """Analyze tickers and print trading signals."""
        results = []
        for ticker in self.tickers:
            df = self.db.fetch_ticker(ticker)
            if df.empty:
                continue
            df = add_indicators(df)
            levels = support_resistance(df)
            last = df.iloc[-1]
            price = last['close']
            if levels['support'] == 0 and levels['resistance'] == 0:
                continue
            near_support = abs(price - levels['support']) / price < 0.02
            near_resistance = abs(price - levels['resistance']) / price < 0.02
            if last['RSI14'] > 70 or last['RSI14'] < 30 or near_support or near_resistance:
                results.append({
                    'ticker': ticker,
                    'price': price,
                    'RSI14': last['RSI14'],
                    'support': levels['support'],
                    'resistance': levels['resistance'],
                    'near_support': near_support,
                    'near_resistance': near_resistance
                })
        return results

    def close(self):
        self.db.close()
