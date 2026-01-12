from data.db_connection import get_connection


def insert_prices(rows):
    """
    rows = [
      {
        asset_id:int,
        date:date,
        open,high,low,close,volume,
        source
      }
    ]
    """

    conn = get_connection()
    cur = conn.cursor()

    q = """
    INSERT INTO stocks.prices
    (asset_id,date,open,high,low,close,volume,source,quality_score)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
    ON CONFLICT DO NOTHING
    """

    for r in rows:
        cur.execute(q,(
            r["asset_id"],r["date"],
            r["open"],r["high"],r["low"],r["close"],
            r["volume"],r["source"],
            100 if r["source"]=="polygon" else 50
        ))

    conn.commit()
    conn.close()

def insert_intraday(rows):
    """
    rows = [
      (
        asset_id,
        datetime,
        open,high,low,close,volume,
        interval,
        source
      )
    ]
    """

    conn = get_connection()
    cur = conn.cursor()

    q = """
    INSERT INTO stocks.stock_intraday
    (asset_id, datetime, open, high, low, close, volume, interval, source)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
    ON CONFLICT DO NOTHING
    """

    cur.executemany(q, rows)

    conn.commit()
    conn.close()
