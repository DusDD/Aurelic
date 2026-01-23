from __future__ import annotations
from datetime import date, timedelta

from .db_calls import get_prices_daily, get_intraday
from .timeframes import TIMEFRAME_BY_KEY, start_date_for_days, start_dt_for_days


def get_line_series(token: str, canonical_symbol: str, timeframe_key: str):
    """
    Returns:
    {
      "symbol": "AAPL",
      "timeframe": "1y",
      "kind": "daily"|"intraday",
      "points": [("2026-01-01", 123.4), ...] OR [("2026-01-01T10:15:00", 123.4), ...]
    }
    """
    tf = TIMEFRAME_BY_KEY.get(timeframe_key)
    if not tf:
        raise ValueError(f"Unknown timeframe: {timeframe_key}")

    if tf.kind == "daily":
        start = start_date_for_days(tf.lookback_days)
        rows = get_prices_daily(
            token=token,
            canonical_symbol=canonical_symbol,
            source=tf.source,
            start_date=start,
        )
        points = [(str(d), float(c)) for (d, c) in rows if c is not None]

    else:
        start = start_dt_for_days(tf.lookback_days)
        rows = get_intraday(
            token=token,
            canonical_symbol=canonical_symbol,
            source=tf.source,
            interval=tf.interval or "15min",
            start_dt=start,
        )
        points = [(dt.isoformat(timespec="seconds"), float(c)) for (dt, c) in rows if c is not None]

    return {
        "symbol": canonical_symbol,
        "timeframe": tf.key,
        "kind": tf.kind,
        "source": tf.source,
        "points": points,
    }

def get_line_series_range(token: str, canonical_symbol: str, source: str, start: date, end: date):
    rows = get_prices_daily(
        token=token,
        canonical_symbol=canonical_symbol,
        source=source,
        start_date=start,
        end_date=end,
    )
    points = [(str(d), float(c)) for (d, c) in rows if c is not None]
    return {
        "symbol": canonical_symbol,
        "timeframe": "custom",
        "kind": "daily",
        "source": source,
        "points": points,
    }

def get_polygon_last_7d_daily(token: str, canonical_symbol: str):
    end = date.today()
    start = end - timedelta(days=14)  # 14 -> wegen Wochenenden sicher genug, wir schneiden nachher
    rows = get_prices_daily(
        token=token,
        canonical_symbol=canonical_symbol,
        source="polygon",
        start_date=start,
        end_date=end,
    )

    # nur die letzten 7 Datenpunkte nehmen (Handelstage)
    rows = rows[-7:]

    points = [(str(d), float(c)) for (d, c) in rows if c is not None]
    return {
        "symbol": canonical_symbol,
        "timeframe": "polygon_7d",
        "kind": "daily",
        "source": "polygon",
        "points": points,
    }