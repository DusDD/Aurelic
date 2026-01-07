import yfinance as yf
from data import insert_stock_prices
from config import SYMBOLS


def backfill_symbol(symbol):
    df = yf.download(symbol, period="max", auto_adjust=False)

    rows = []
    for date, row in df.iterrows():
        rows.append((
            symbol,
            date.date(),
            float(row["Open"].iloc[0]),
            float(row["High"].iloc[0]),
            float(row["Low"].iloc[0]),
            float(row["Close"].iloc[0]),
            int(row["Volume"].iloc[0]),
            "yahoo",
        ))

    insert_stock_prices(rows)
    print(f"Backfilled {symbol}: {len(rows)} rows")


if __name__ == "__main__":
    for symbol in SYMBOLS:
        backfill_symbol(symbol)