import yfinance as yf
import logging

log = logging.getLogger(__name__)


def fetch_historical(asset_id, symbol):

    df = yf.download(symbol, period="max", auto_adjust=False)

    rows = []

    for date, row in df.iterrows():
        rows.append({
            "asset_id": asset_id,
            "date": date.date(),
            "open": float(row["Open"].item()),
            "high": float(row["High"].item()),
            "low": float(row["Low"].item()),
            "close": float(row["Close"].item()),
            "volume": int(row["Volume"].item()),
            "source": "yahoo"
        })

    return rows
