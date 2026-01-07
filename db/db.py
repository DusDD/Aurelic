import psycopg2
from psycopg2.extras import execute_batch
from db.db import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD


def get_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )


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