# src/daily_pull_alphavantage.py

import requests
from datetime import datetime
import time
import logging
import pandas_market_calendars as mcal
from db import insert_stock_prices
from config import SYMBOLS, ALPHAVANTAGE_API_KEY

# --------------------------
# Setup logging
# --------------------------
logging.basicConfig(
    filename='daily_pull.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

# --------------------------
# Market calendar check
# --------------------------
def is_market_open_today():
    nyse = mcal.get_calendar('NYSE')
    today = datetime.today().date()
    schedule = nyse.schedule(start_date=today, end_date=today)
    return not schedule.empty

# --------------------------
# Fetch daily data from Alpha Vantage
# --------------------------
def fetch_daily(symbol):
    URL = "https://www.alphavantage.co/query"
    params = {
        "function": "TIME_SERIES_DAILY_ADJUSTED",
        "symbol": symbol,
        "apikey": ALPHAVANTAGE_API_KEY,
        "outputsize": "compact",  # only recent data
    }

    try:
        r = requests.get(URL, params=params)
        r.raise_for_status()
        data = r.json()
        ts = data.get("Time Series (Daily)", {})

        if not ts:
            logging.warning(f"No data returned for {symbol}")
            return

        rows = []
        for date, values in ts.items():
            rows.append((
                symbol,
                date,
                float(values["1. open"].iloc[0]),
                float(values["2. high"].iloc[0]),
                float(values["3. low"].iloc[0]),
                float(values["4. close"].iloc[0]),
                int(values["6. volume"].iloc[0]),
                "alphavantage"
            ))

        insert_stock_prices(rows)
        logging.info(f"Inserted {len(rows)} rows for {symbol}")

    except Exception as e:
        logging.error(f"Error fetching {symbol}: {e}")

# --------------------------
# Main function
# --------------------------
def main():
    if not is_market_open_today():
        logging.info("Market is closed today. Skipping daily pull.")
        return

    logging.info("Starting daily pull for all symbols...")
    for symbol in SYMBOLS:
        fetch_daily(symbol)
        # Free Alpha Vantage API limit: 5 requests per minute
        time.sleep(15)  # wait 15 seconds between calls

    logging.info("Daily pull completed.")

# --------------------------
# Entry point
# --------------------------
if __name__ == "__main__":
    main()
