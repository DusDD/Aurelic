import yfinance as yf
from db import get_connection

SYMBOLS = [
    "AAPL",
    "MSFT",
    "GOOGL",
]

START_DATE = "2005-01-01"
SOURCE = "yahoo"

def backfill_symbol(symbol):
    df = yf.download(
        symbol,
        start=START_DATE,
        auto_adjust=False,
        progress=False
    )

    if df.empty:
        print(f"⚠️ Keine Daten für {symbol}")
        return

    df.reset_index(inplace=True)

    conn = get_connection()
    cur = conn.cursor()

    for _, row in df.iterrows():
        cur.execute("""
            INSERT INTO stock_prices
            (symbol, date, open, high, low, close, adj_close, volume, source)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT DO NOTHING
        """, (
            symbol,
            row["Date"].date(),
            row["Open"],
            row["High"],
            row["Low"],
            row["Close"],
            row["Adj Close"],
            int(row["Volume"]),
            SOURCE
        ))

    conn.commit()
    cur.close()
    conn.close()

    print(f"✅ Backfill abgeschlossen für {symbol}")

if __name__ == "__main__":
    for sym in SYMBOLS:
        backfill_symbol(sym)