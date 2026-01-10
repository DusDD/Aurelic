from data.db_connection import get_connection


def insert_prices(rows: list[dict]):
    """
    Erwartet Liste von Dicts
    """
    if not rows:
        return

    conn = get_connection()
    cursor = conn.cursor()

    values = [
        (
            r["symbol"],
            r["date"],
            r["open"],
            r["high"],
            r["low"],
            r["close"],
            r["volume"],
            r["source"]
        )
        for r in rows
    ]

    cursor.executemany("""
        INSERT INTO stocks.stock_prices
        (symbol, date, open, high, low, close, volume, source)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (symbol, date)
        DO NOTHING
    """, values)

    conn.commit()
    cursor.close()
    conn.close()
