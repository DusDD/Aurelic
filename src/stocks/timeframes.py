# src/stocks/timeframes.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, date

@dataclass(frozen=True)
class TimeframeSpec:
    key: str
    label: str
    source: str            # 'yahoo' | 'polygon'
    kind: str              # 'daily' | 'intraday'
    lookback_days: int     # used to compute start date/time
    interval: str | None = None  # intraday only (e.g. '15min')

# UI order matters
TIMEFRAMES: list[TimeframeSpec] = [
    # Yahoo (daily)
    TimeframeSpec("max",  "MAX", "yahoo",   "daily",    365 * 20),
    TimeframeSpec("5y",   "5Y",  "yahoo",   "daily",    365 * 5),
    TimeframeSpec("3y",   "3Y",  "yahoo",   "daily",    365 * 3),
    TimeframeSpec("1y",   "1Y",  "yahoo",   "daily",    365 * 1),
    TimeframeSpec("6m",   "6M",  "yahoo",   "daily",    183),

    # Polygon (daily)
    TimeframeSpec("30d",  "30D", "polygon", "daily",    30),

    # Polygon (intraday)
    TimeframeSpec("7d_i", "7D i", "polygon", "intraday", 7,  interval="15min"),
    TimeframeSpec("1d_i", "1D i", "polygon", "intraday", 1,  interval="5min"),
]

TIMEFRAME_BY_KEY = {t.key: t for t in TIMEFRAMES}

def start_date_for_days(days: int) -> date:
    return (datetime.utcnow() - timedelta(days=days)).date()

def start_dt_for_days(days: int) -> datetime:
    return datetime.utcnow() - timedelta(days=days)
