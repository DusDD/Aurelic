import requests
import time
import logging
from datetime import datetime

from data.repositories.stock_repo import insert_intraday
from data.config import POLYGON_API_KEY
from data.utils.market_days import get_last_trading_days
from data.repositories.asset_repo import get_assets_for_provider

INTERVAL_MIN = 15
INTERVAL_LABEL = "15min"

# Logger
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# --------------------------------
# Polygon Fetch
# --------------------------------
def fetch_intraday_day(asset_id, symbol, trading_day):

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
            log.warning(f"No intraday data {symbol} {trading_day}")
            return []

        rows = []

        for bar in data["results"]:
            ts = datetime.fromtimestamp(bar["t"]/1000)

            rows.append((
                asset_id,
                ts,
                bar["o"], bar["h"], bar["l"], bar["c"],
                bar["v"],
                INTERVAL_LABEL,
                "polygon"
            ))

        return rows

    except Exception as e:
        log.error(f"{symbol} {trading_day}: {e}")
        return []


# --------------------------------
# Main
# --------------------------------
def main():

    days = get_last_trading_days(n=7)
    assets = get_assets_for_provider("polygon")

    log.info(f"Intraday backfill: {len(assets)} assets")

    all_rows = []

    for a in assets:
        asset_id = a["asset_id"]
        symbol = a["symbol"]

        log.info(f"Symbol {symbol}")

        for day in days:
            log.info(f"  Day {day}")
            rows = fetch_intraday_day(asset_id, symbol, day)
            all_rows.extend(rows)
            time.sleep(12)

    insert_intraday(all_rows)
    log.info(f"Inserted {len(all_rows)} intraday rows")


if __name__ == "__main__":
    main()
