import time
import logging
from datetime import datetime, timedelta
import pandas_market_calendars as mcal

from data.symbols import SYMBOLS, MISSING
from data.providers.polygon import fetch_daily
from data.providers.yahoo import fetch_historical
from data.repositories.stock_repo import insert_prices

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def get_last_trading_days(n=30):
    nyse = mcal.get_calendar("NYSE")
    today = datetime.utcnow().date()
    schedule = nyse.schedule(
        start_date=today - timedelta(days=n*2),
        end_date=today
    )
    return [d.date() for d in schedule.index[-n:]]


def polygon_backfill(days=30):
    trading_days = get_last_trading_days(days)
    all_rows = []

    for s in SYMBOLS:
        symbol = s["symbol"]  # <-- nur der String
        log.info(f"Polygon backfill {symbol}")

        for day in trading_days:
            data = fetch_daily(symbol, day)
            if data:
                all_rows.append(data)

            time.sleep(12)

    insert_prices(all_rows)
    log.info(f"Inserted {len(all_rows)} rows")


def yahoo_backfill():
    for s in SYMBOLS:
        symbol = s["symbol"]  # <-- nur der String
        rows = fetch_historical(symbol)
        insert_prices(rows)


if __name__ == "__main__":
#    yahoo_backfill()
    polygon_backfill(days=30)
