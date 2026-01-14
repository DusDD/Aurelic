import time
import logging
from datetime import datetime, timedelta
import pandas_market_calendars as mcal

from z_outdated.db_insert import insert_intraday
from data.db_connection import get_connection
from data.providers.polygon import fetch_intraday

logging.basicConfig(level=logging.INFO)


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


def main():
    trading_day = get_last_trading_day()

    if not trading_day:
        logging.info("No trading day found")
        return

    symbols = get_active_symbols()
    all_rows = []

    logging.info(
        f"Intraday refresh started "
        f"({len(symbols)} symbols | {trading_day})"
    )

    for sym in symbols:
        logging.info(f"Fetching intraday {sym}")

        rows = fetch_intraday(sym, trading_day)
        all_rows.extend(rows)

        time.sleep(12)  # Polygon Free Tier Schutz

    if all_rows:
        insert_intraday(all_rows)
        logging.info(f"Inserted {len(all_rows)} intraday rows")
    else:
        logging.info("No intraday rows fetched")


if __name__ == "__main__":
    main()
