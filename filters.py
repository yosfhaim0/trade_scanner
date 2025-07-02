from typing import List, Dict


def filter_by_sector(stocks: List[Dict], sector: str) -> List[Dict]:
    """Return stocks that belong to the provided sector."""
    return [s for s in stocks if s.get("sector") == sector]


def filter_options_only(stocks: List[Dict]) -> List[Dict]:
    """Return only stocks which have options contracts available."""
    return [s for s in stocks if s.get("has_options")]
