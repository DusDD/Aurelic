import requests
import time
import logging
from datetime import datetime, timedelta
import pandas_market_calendars as mcal

from data.db_insert import insert_stock_prices
from data.config import SYMBOLS, POLYGON_API_KEY

# --------------------------
# Setup logging
# --------------------------
logging.basicConfig(
    filename="daily_pull.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# --------------------------
# Market calendar
# --------------------------
def get_last_trading_day():
    nyse = mcal.get_calendar("NYSE")
    today = datetime.utcnow().date()
    schedule = nyse.schedule(
        start_date=today - timedelta(days=7),
        end_date=today
    )
    if schedule.empty:
        return None
    return schedule.index[-1].date()

# --------------------------
# Fetch daily bar from Polygon
# --------------------------
def fetch_daily(symbol, trading_day):
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
            logging.warning(f"No data for {symbol} on {trading_day}")
            return

        bar = data["results"][0]

        row = [(
            symbol,
            trading_day.isoformat(),
            bar["o"],  # open
            bar["h"],  # high
            bar["l"],  # low
            bar["c"],  # close
            bar["v"],  # volume
            "polygon"
        )]

        insert_stock_prices(row)
        logging.info(f"Inserted daily bar for {symbol} ({trading_day})")

    except Exception as e:
        logging.error(f"Polygon error for {symbol}: {e}")

# --------------------------
# Main
# --------------------------
def main():
    trading_day = get_last_trading_day()

    if not trading_day:
        logging.info("No trading day found. Skipping.")
        return

    logging.info(f"Starting Polygon daily pull for {trading_day}")

    for symbol in SYMBOLS:
        fetch_daily(symbol, trading_day)
        time.sleep(1)  # Polygon Free Tier ist entspannt

    logging.info("Polygon daily pull completed")

# --------------------------
# Entry
# --------------------------
if __name__ == "__main__":
    main()