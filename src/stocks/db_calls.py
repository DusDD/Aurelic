from data.db_connection import get_connection
from ..auth.guard import require_auth

# -----------------------------------
# Stock Prices
# -----------------------------------
def get_stock_prices(token: str, symbol: str):
    """
    Liefert alle historischen Preise einer Aktie
    """
    require_auth(token)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT date, open, high, low, close, volume
        FROM stocks.stock_prices
        WHERE symbol = %s
        ORDER BY date DESC
    """, (symbol,))

    rows = cursor.fetchall()
    conn.close()
    return rows


def get_latest_closes(symbol: str, limit: int = 2):
    """
    Liefert die letzten N Schlusskurse
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT date, close
        FROM stocks.stock_prices
        WHERE symbol = %s
        ORDER BY date DESC
        LIMIT %s
    """, (symbol, limit))

    rows = cursor.fetchall()
    conn.close()
    return rows


# -----------------------------------
# Symbols
# -----------------------------------
def get_all_symbols(token: str):
    """
    Liefert alle verfügbaren Symbole
    """
    require_auth(token)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT symbol
        FROM stocks.stock_prices
        ORDER BY symbol
    """)

    rows = [row[0] for row in cursor.fetchall()]
    conn.close()
    return rows


# -----------------------------------
# Favoriten
# -----------------------------------
def get_user_favorites(token: str):
    """
    Liefert Favoriten des Users
    """
    user_id = require_auth(token)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT symbol
        FROM stocks.favorites
        WHERE user_id = %s
    """, (user_id,))

    rows = [row[0] for row in cursor.fetchall()]
    conn.close()
    return rows
