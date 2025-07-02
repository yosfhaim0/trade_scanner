import json
from typing import List
from pathlib import Path

from stock_list import load_stock_list


def get_all_sectors(path: str = "stocks.json") -> List[str]:
    """Return a sorted list of all unique sectors from cached stock data."""
    stocks = load_stock_list(path)
    sectors = {stock.get("sector") for stock in stocks if stock.get("sector")}
    return sorted(sectors)
