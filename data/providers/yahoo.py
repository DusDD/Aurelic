import yfinance as yf
import logging

log = logging.getLogger(__name__)


def fetch_historical(symbol):
    if isinstance(symbol, dict):
        symbol = symbol.get("symbol")
    if not isinstance(symbol, str):
        raise ValueError(f"Expected string symbol, got {type(symbol)}")

    df = yf.download(symbol, period="max", auto_adjust=False, timeout=60)

    rows = []

    for date, row in df.iterrows():
        rows.append({
            "symbol": symbol,
            "date": date.date(),
            "open": float(row["Open"].iloc[0]),
            "high": float(row["High"].iloc[0]),
            "low": float(row["Low"].iloc[0]),
            "close": float(row["Close"].iloc[0]),
            "volume": int(row["Volume"].iloc[0]),
            "source": "yahoo"
        })

    log.info(f"Fetched {len(rows)} rows for {symbol}")
    return rows
