from data.db_connection import get_connection
from ..auth.guard import require_auth


# -----------------------------------
# Helper
# -----------------------------------
def _get_asset_id(symbol: str):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT a.asset_id
        FROM stocks.assets a
        JOIN stocks.asset_symbols s
            ON a.asset_id = s.asset_id
        WHERE s.provider_symbol = %s
    """, (symbol,))

    row = cur.fetchone()
    conn.close()

    if not row:
        raise ValueError(f"Unknown symbol: {symbol}")

    return row[0]


# -----------------------------------
# Stock Prices
# -----------------------------------
def get_stock_prices(token: str, symbol: str):
    require_auth(token)

    asset_id = _get_asset_id(symbol)

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT date, open, high, low, close, volume
        FROM stocks.prices
        WHERE asset_id = %s
        ORDER BY date DESC
    """, (asset_id,))

    rows = cur.fetchall()
    conn.close()
    return rows


def get_latest_closes(symbol: str, limit: int = 2):
    asset_id = _get_asset_id(symbol)

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT date, close
        FROM stocks.prices
        WHERE asset_id = %s
        ORDER BY date DESC
        LIMIT %s
    """, (asset_id, limit))

    rows = cur.fetchall()
    conn.close()
    return rows


# -----------------------------------
# Symbols
# -----------------------------------
def get_all_symbols(token: str):
    require_auth(token)

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT provider_symbol
        FROM stocks.asset_symbols
        ORDER BY provider_symbol
    """)

    rows = [r[0] for r in cur.fetchall()]
    conn.close()
    return rows


# -----------------------------------
# Favoriten
# -----------------------------------
def get_user_favorites(token: str):
    user_id = require_auth(token)

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT s.provider_symbol
        FROM stocks.favorites f
        JOIN stocks.asset_symbols s
            ON f.asset_id = s.asset_id
        WHERE f.user_id = %s
    """, (user_id,))

    rows = [r[0] for r in cur.fetchall()]
    conn.close()
    return rows


# -----------------------------------
# Intraday
# -----------------------------------
def get_intraday(token, symbol, interval="15min", limit=200):
    require_auth(token)

    asset_id = _get_asset_id(symbol)

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT datetime, open, high, low, close, volume
        FROM stocks.stock_intraday
        WHERE asset_id=%s AND interval=%s
        ORDER BY datetime DESC
        LIMIT %s
    """,(asset_id,interval,limit))

    rows = cur.fetchall()
    conn.close()
    return rows
