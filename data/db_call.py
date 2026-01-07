from .db_connection import get_connection
from src.auth.guard import require_auth


def get_stock_prices(token: str, symbol: str):
    user_id = require_auth(token)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT date, open, high, low, close, volume
        FROM stocks.stock_prices
        WHERE symbol = %s
        ORDER BY date DESC
        """,
        (symbol,)
    )

    rows = cursor.fetchall()
    conn.close()

    return rows