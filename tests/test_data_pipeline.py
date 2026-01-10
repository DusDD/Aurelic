from data.providers.polygon import fetch_daily
from data.symbols import SYMBOLS
from datetime import date


def test_polygon_provider():
    data = fetch_daily(SYMBOLS[0], date.today())
    assert data is None or "close" in data
