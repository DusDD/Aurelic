# src/stocks/calculations.py
from __future__ import annotations

from .db_calls import get_all_assets, get_latest_closes, get_user_favorites


def calculate_top_movers(symbols: list[str], source: str, top_n: int = 3):
    movers = []

    for symbol in symbols:
        prices = get_latest_closes(symbol, source=source, limit=2)
        if len(prices) < 2:
            continue

        latest_close = float(prices[0][1])
        prev_close = float(prices[1][1])
        if prev_close == 0:
            continue

        change_pct = ((latest_close - prev_close) / prev_close) * 100.0
        movers.append((symbol, round(prev_close, 2), round(latest_close, 2), round(change_pct, 2)))

    movers.sort(key=lambda x: abs(x[3]), reverse=True)
    return movers[:top_n]


def get_top_movers_overall(token: str, top_n: int = 3):
    # use canonical symbols from assets
    assets = get_all_assets(token)
    symbols = [a[0] for a in assets]
    return calculate_top_movers(symbols, source="yahoo", top_n=top_n)


def get_top_movers_favorites(token: str, top_n: int = 3):
    favorites = get_user_favorites(token)
    return calculate_top_movers(favorites, source="yahoo", top_n=top_n)
