# src/data/db_calls.py
from data.db_connection import get_connection
from ..auth.guard import require_auth

# -----------------------------------
# Stock Prices
# -----------------------------------
def get_stock_prices(token: str, symbol: str):
    """
    Liefert alle historischen Preise einer Aktie (absteigend nach Datum)
    """
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

    cursor.execute(
        """
        SELECT DISTINCT symbol 
        FROM stocks.stock_prices 
        ORDER BY symbol;

        """
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


# -----------------------------------
# Favoriten
# -----------------------------------
def get_user_favorites(token: str):
    """
    Liefert die Symbole, die der Nutzer als Favorit markiert hat
    """
    user_id = require_auth(token)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT symbol
        FROM stocks.favorites
        WHERE user_id = %s
        """,
        (user_id,)
    )
    rows = [row[0] for row in cursor.fetchall()]
    conn.close()
    return rows


# -----------------------------------
# Top Mover Overall
# -----------------------------------
def get_top_movers_overall(token: str, limit: int = 3):
    """
    Berechnet die Top X Movers (prozentuale Veränderung vom Vortag)
    """
    require_auth(token)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        WITH latest_prices AS (
            SELECT symbol, close,
                   LAG(close) OVER (PARTITION BY symbol ORDER BY date) AS prev_close
            FROM stocks.stock_prices
        )
        SELECT symbol, close, prev_close,
               ROUND((close - prev_close) / prev_close * 100, 2) AS pct_change
        FROM latest_prices
        WHERE prev_close IS NOT NULL
        ORDER BY pct_change DESC
        LIMIT %s
        """,
        (limit,)
    )

    rows = cursor.fetchall()
    conn.close()
    # Rückgabe: [(symbol, close, prev_close, pct_change), ...]
    return rows


# -----------------------------------
# Top Mover Favoriten
# -----------------------------------
def get_top_movers_favorites(token: str, limit: int = 3):
    """
    Berechnet die Top X Movers innerhalb der Favoritenliste des Users
    """
    user_id = require_auth(token)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        WITH latest_prices AS (
            SELECT sp.symbol, sp.close,
                   LAG(sp.close) OVER (PARTITION BY sp.symbol ORDER BY sp.date) AS prev_close
            FROM stocks.stock_prices sp
            JOIN stocks.favorites f ON f.symbol = sp.symbol
            WHERE f.user_id = %s
        )
        SELECT symbol, close, prev_close,
               ROUND((close - prev_close) / prev_close * 100, 2) AS pct_change
        FROM latest_prices
        WHERE prev_close IS NOT NULL
        ORDER BY pct_change DESC
        LIMIT %s
        """,
        (user_id, limit)
    )

    rows = cursor.fetchall()
    conn.close()
    # Rückgabe: [(symbol, close, prev_close, pct_change), ...]
    return rows
