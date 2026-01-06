import requests
from datetime import datetime, timedelta
import pandas_market_calendars as mcal
import logging
import time

from db import insert_stock_prices
from config import SYMBOLS, POLYGON_API_KEY

# --------------------------
# Logging
# --------------------------
logging.basicConfig(level=logging.INFO)

# --------------------------
# NYSE Trading Days
# --------------------------
def get_last_trading_days(n=30):
    """
    Gibt die letzten n Handelstage zurück.
    Du kannst n beliebig erhöhen, z.B. 30 Tage für Backfill.
    """
    nyse = mcal.get_calendar("NYSE")
    today = datetime.utcnow().date()
    schedule = nyse.schedule(
        start_date=today - timedelta(days=n*2),  # Puffer, falls Wochenende/Feiertag
        end_date=today
    )
    return [d.date() for d in schedule.index[-n:]]

# --------------------------
# Polygon API Fetch
# --------------------------
def fetch_polygon_daily(symbol, trading_day):
    url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/day/{trading_day}/{trading_day}"
    headers = {"Authorization": f"Bearer {POLYGON_API_KEY}"}

    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()

        if data.get("resultsCount", 0) == 0:
            logging.warning(f"No data for {symbol} on {trading_day}")
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
            "source": "polygon",
        }

    except Exception as e:
        logging.error(f"Error fetching {symbol} on {trading_day}: {e}")
        return None

# --------------------------
# Main Backfill Routine
# --------------------------
def main():
    trading_days = get_last_trading_days(n=30)  # z.B. letzte 30 Handelstage
    all_rows = []

    for symbol in SYMBOLS:
        logging.info(f"Start backfill for {symbol}")
        for day in trading_days:
            data = fetch_polygon_daily(symbol, day)
            if data:
                all_rows.append((
                    data["symbol"],
                    data["date"],
                    data["open"],
                    data["high"],
                    data["low"],
                    data["close"],
                    data["volume"],
                    data["source"]
                ))
            time.sleep(13)  # Polygon Free Tier schonend

    insert_stock_prices(all_rows)
    logging.info(f"Inserted {len(all_rows)} rows for {len(SYMBOLS)} symbols")

# --------------------------
# Entry Point
# --------------------------
if __name__ == "__main__":
    main()