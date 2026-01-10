import requests
import time
import logging
from datetime import datetime

from data.db_insert import insert_intraday
from data.db_connection import get_connection
from data.config import POLYGON_API_KEY
from data.utils.market_days import get_last_trading_days

INTERVAL_MIN = 15
INTERVAL_LABEL = "15min"

logging.basicConfig(level=logging.INFO)


# --------------------------------
# Symbols
# --------------------------------
def get_active_symbols():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT symbol
        FROM stocks.symbols
        WHERE active = true
    """)
    rows = [r[0] for r in cur.fetchall()]
    conn.close()
    return rows


# --------------------------------
# Polygon Fetch
# --------------------------------
def fetch_intraday_day(symbol, trading_day):

    url = (
        f"https://api.polygon.io/v2/aggs/ticker/{symbol}"
        f"/range/{INTERVAL_MIN}/minute/"
        f"{trading_day}/{trading_day}"
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
            logging.warning(f"No intraday data {symbol} {trading_day}")
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
        logging.error(f"{symbol} {trading_day}: {e}")
        return []


# --------------------------------
# Main
# --------------------------------
def main():
    days = get_last_trading_days(n=7)
    symbols = get_active_symbols()

    logging.info(f"Backfill {len(symbols)} symbols, days={days}")

    all_rows = []

    for sym in symbols:
        logging.info(f"Symbol {sym}")

        for day in days:
            logging.info(f"  Day {day}")
            rows = fetch_intraday_day(sym, day)
            all_rows.extend(rows)
            time.sleep(12)  # free tier safe

    insert_intraday(all_rows)
    logging.info(f"Inserted {len(all_rows)} intraday rows")


if __name__ == "__main__":
    main()
