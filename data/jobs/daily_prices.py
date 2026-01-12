import time
import logging
from datetime import datetime, timedelta
import pandas_market_calendars as mcal

from data.utils.symbols import SYMBOLS
from data.providers.polygon import fetch_daily
from data.repositories.stock_repo import insert_prices

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def get_last_trading_day():
    nyse = mcal.get_calendar("NYSE")
    today = datetime.utcnow().date()
    schedule = nyse.schedule(
        start_date=today - timedelta(days=7),
        end_date=today
    )
    return schedule.index[-1].date()


def main():
    trading_day = get_last_trading_day()
    log.info(f"Daily pull for {trading_day}")

    rows = []

    for symbol in SYMBOLS:
        data = fetch_daily(symbol, trading_day)
        if data:
            rows.append(data)

        time.sleep(1)

    insert_prices(rows)
    log.info("Daily pull done")


if __name__ == "__main__":
    main()
