from psycopg2.extras import execute_batch
from data.db_connection import get_connection

def insert_stock_prices(rows):
    sql = """
    INSERT INTO stock_prices
    (symbol, date, open, high, low, close, volume, source)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (symbol, date) DO NOTHING;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            execute_batch(cur, sql, rows)