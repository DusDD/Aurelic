from psycopg2.extras import execute_batch
from data.db_connection import get_connection

def insert_stock_prices(rows):
    sql = """
    INSERT INTO stocks.stock_prices
    (symbol, date, open, high, low, close, volume, source)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (symbol, date) DO NOTHING;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            execute_batch(cur, sql, rows)

def insert_intraday(rows):
    conn = get_connection()
    cur = conn.cursor()

    cur.executemany("""
        INSERT INTO stocks.stock_intraday
        (symbol, datetime, open, high, low, close, volume, interval, source)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT DO NOTHING
    """, rows)

    conn.commit()
    conn.close()
