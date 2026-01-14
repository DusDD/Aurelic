from .db_calls import get_stock_prices


def get_price_timeseries(token: str, symbol: str, limit: int = 100):
    """
    Liefert Kurs-Zeitreihe für Charts
    Rückgabe:
    {
        "symbol": "AAPL",
        "dates": [...],
        "closes": [...],
        "opens": [...],
        "highs": [...],
        "lows": [...],
        "volumes": [...]
    }
    """

    rows = get_stock_prices(token, symbol)

    # Optional: Limit
    rows = rows[:limit]

    dates = []
    closes = []
    opens = []
    highs = []
    lows = []
    volumes = []

    for row in reversed(rows):  # Chronologisch
        date, open_, high, low, close, volume = row

        dates.append(str(date))
        closes.append(float(close))
        opens.append(float(open_))
        highs.append(float(high))
        lows.append(float(low))
        volumes.append(int(volume))

    return {
        "symbol": symbol,
        "dates": dates,
        "closes": closes,
        "opens": opens,
        "highs": highs,
        "lows": lows,
        "volumes": volumes
    }


def get_candlestick_data(token: str, symbol: str, limit: int = 100):
    """
    Liefert OHLC-Daten für Candlestick-Charts

    Rückgabe:
    {
        "symbol": "AAPL",
        "data": [
            {
                "date": "2026-01-05",
                "open": 270.64,
                "high": 271.51,
                "low": 266.14,
                "close": 267.26,
                "volume": 45633196
            },
            ...
        ]
    }
    """

    rows = get_stock_prices(token, symbol)
    rows = rows[:limit]

    candles = []

    for row in reversed(rows):
        date, open_, high, low, close, volume = row

        candles.append({
            "date": str(date),
            "open": float(open_),
            "high": float(high),
            "low": float(low),
            "close": float(close),
            "volume": int(volume)
        })

    return {
        "symbol": symbol,
        "data": candles
    }