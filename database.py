import sqlite3
from pathlib import Path
import pandas as pd


class Database:
    """Simple SQLite wrapper for storing market data."""

    def __init__(self, db_path: str = "market.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self._create_schema()

    def _create_schema(self):
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                datetime TEXT NOT NULL,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume REAL
            )
            """
        )
        self.conn.commit()

    def insert_dataframe(self, df: pd.DataFrame):
        df = df[["Ticker", "Date", "Open", "High", "Low", "Close", "Volume"]]
        df.columns = ["ticker", "datetime", "open", "high", "low", "close", "volume"]
        df.to_sql("prices", self.conn, if_exists="append", index=False)

    def fetch_ticker(self, ticker: str) -> pd.DataFrame:
        query = "SELECT * FROM prices WHERE ticker = ? ORDER BY datetime"
        return pd.read_sql_query(query, self.conn, params=(ticker,))

    def close(self):
        self.conn.close()
