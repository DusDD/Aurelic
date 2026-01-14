import time
import logging
from data.repositories.asset_repo import get_assets_for_provider
from data.providers.polygon import fetch_daily
from data.providers.yahoo import fetch_historical
from data.repositories.stock_repo import insert_prices
from data.utils.market_days import get_last_trading_days

# ---------------------------
# Logger konfigurieren
# ---------------------------
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def polygon_backfill(days=30):

    assets = get_assets_for_provider("polygon")
    trading_days = get_last_trading_days(days)
    all_rows = []

    for a in assets:
        log.info(f"Polygon {a['symbol']}")

        for d in trading_days:
            r = fetch_daily(a["asset_id"], a["symbol"], d)
            if r:
                all_rows.append(r)
            time.sleep(12)

    insert_prices(all_rows)


def yahoo_backfill():

    assets = get_assets_for_provider("yahoo")

    for a in assets:
        rows = fetch_historical(a["asset_id"], a["symbol"])
        insert_prices(rows)

if __name__ == "__main__":
#    yahoo_backfill()
    polygon_backfill()