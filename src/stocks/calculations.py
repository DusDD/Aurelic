from .db_calls import (
    get_latest_closes,
    get_all_symbols,
    get_user_favorites
)


# -----------------------------------
# Core Logic
# -----------------------------------
def calculate_top_movers(symbols: list, top_n: int = 3):
    """
    Berechnet Top-Movers anhand der letzten 2 Schlusskurse
    """
    movers = []

    for symbol in symbols:
        prices = get_latest_closes(symbol, limit=2)

        if len(prices) < 2:
            continue

        latest_close = prices[0][1]
        prev_close = prices[1][1]

        change_pct = ((latest_close - prev_close) / prev_close) * 100

        movers.append((
            symbol,
            round(prev_close, 2),
            round(latest_close, 2),
            round(change_pct, 2)
        ))

    movers.sort(key=lambda x: abs(x[3]), reverse=True)
    return movers[:top_n]


# -----------------------------------
# Public API
# -----------------------------------
def get_top_movers_overall(token: str, top_n: int = 3):
    symbols = get_all_symbols(token)
    return calculate_top_movers(symbols, top_n)


def get_top_movers_favorites(token: str, top_n: int = 3):
    favorites = get_user_favorites(token)
    return calculate_top_movers(favorites, top_n)
