import requests
import logging
from datetime import datetime, timedelta
from data.config import POLYGON_API_KEY

log = logging.getLogger(__name__)

INTERVAL_MIN = 15
INTERVAL_LABEL = "15min"

def fetch_daily(symbol: str, trading_day):
    """
    Holt Tageskerze für EIN Symbol an EINEM Tag
    """
    url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/day/{trading_day}/{trading_day}"

    params = {
        "adjusted": "true",
        "sort": "asc",
        "limit": 1,
        "apiKey": POLYGON_API_KEY
    }

    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()

        if data.get("resultsCount", 0) == 0:
            log.warning(f"No data for {symbol} on {trading_day}")
            return None

        bar = data["results"][0]

        return {
            "symbol": symbol,
            "date": trading_day,
            "open": bar["o"],
            "high": bar["h"],
            "low": bar["l"],
            "close": bar["c"],
            "volume": bar["v"],
            "source": "polygon"
        }

    except Exception as e:
        log.error(f"Polygon error {symbol}: {e}")
        return None


def fetch_intraday(symbol):
    end = datetime.utcnow()
    start = end - timedelta(minutes=INTERVAL_MIN*200)

    url = (
        f"https://api.polygon.io/v2/aggs/ticker/{symbol}"
        f"/range/{INTERVAL_MIN}/minute/"
        f"{start.date()}/{end.date()}"
    )

    params = {
        "adjusted": "true",
        "sort": "asc",
        "limit": 50000,
        "apiKey": POLYGON_API_KEY
    }

    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()

        if "results" not in data:
            logging.warning(f"No intraday data for {symbol}")
            return []

        rows = []

        for bar in data["results"]:
            ts = datetime.fromtimestamp(bar["t"]/1000)

            rows.append((
                symbol,
                ts,
                bar["o"],
                bar["h"],
                bar["l"],
                bar["c"],
                bar["v"],
                INTERVAL_LABEL,
                "polygon"
            ))

        return rows

    except Exception as e:
        logging.error(f"{symbol} intraday error: {e}")
        return []