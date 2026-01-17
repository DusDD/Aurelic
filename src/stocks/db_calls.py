# src/stocks/db_calls.py
from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from data.db_connection import get_connection
from ..auth.guard import require_auth


# -----------------------------------
# Asset lookup
# -----------------------------------
def _get_asset_id_by_canonical(canonical_symbol: str) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT asset_id
        FROM stocks.assets
        WHERE canonical_symbol = %s
        """,
        (canonical_symbol,),
    )
    row = cur.fetchone()
    conn.close()
    if not row:
        raise ValueError(f"Unknown canonical symbol: {canonical_symbol}")
    return int(row[0])


# -----------------------------------
# Assets list (for dropdown)
# -----------------------------------
def get_all_assets(token: str):
    require_auth(token)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT canonical_symbol, COALESCE(name, canonical_symbol) AS name, category
        FROM stocks.assets
        WHERE active = TRUE
        ORDER BY canonical_symbol
        """
    )
    rows = cur.fetchall()
    conn.close()
    # [(symbol, name, category), ...]
    return rows


# -----------------------------------
# Daily prices (historical)
# -----------------------------------
def get_prices_daily(
    token: str,
    canonical_symbol: str,
    source: str,
    start_date: Optional[date] = None,
    limit: Optional[int] = None,
):
    require_auth(token)
    asset_id = _get_asset_id_by_canonical(canonical_symbol)

    conn = get_connection()
    cur = conn.cursor()

    sql = """
        SELECT date, close
        FROM stocks.prices
        WHERE asset_id = %s AND source = %s
    """
    params = [asset_id, source]

    if start_date is not None:
        sql += " AND date >= %s"
        params.append(start_date)

    sql += " ORDER BY date ASC"

    if limit is not None:
        sql += " LIMIT %s"
        params.append(int(limit))

    cur.execute(sql, tuple(params))
    rows = cur.fetchall()
    conn.close()
    return rows  # [(date, close), ...]


def get_latest_closes(canonical_symbol: str, source: str, limit: int = 2):
    asset_id = _get_asset_id_by_canonical(canonical_symbol)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT date, close
        FROM stocks.prices
        WHERE asset_id = %s AND source = %s
        ORDER BY date DESC
        LIMIT %s
        """,
        (asset_id, source, int(limit)),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


# -----------------------------------
# Intraday prices
# -----------------------------------
def get_intraday(
    token: str,
    canonical_symbol: str,
    source: str,
    interval: str,
    start_dt: Optional[datetime] = None,
    limit: Optional[int] = None,
):
    require_auth(token)
    asset_id = _get_asset_id_by_canonical(canonical_symbol)

    conn = get_connection()
    cur = conn.cursor()

    sql = """
        SELECT datetime, close
        FROM stocks.stock_intraday
        WHERE asset_id = %s AND source = %s AND interval = %s
    """
    params = [asset_id, source, interval]

    if start_dt is not None:
        sql += " AND datetime >= %s"
        params.append(start_dt)

    sql += " ORDER BY datetime ASC"

    if limit is not None:
        sql += " LIMIT %s"
        params.append(int(limit))

    cur.execute(sql, tuple(params))
    rows = cur.fetchall()
    conn.close()
    return rows  # [(datetime, close), ...]


# -----------------------------------
# Favorites (kept)
# -----------------------------------
def get_user_favorites(token: str):
    user_id = require_auth(token)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT a.canonical_symbol
        FROM stocks.favorites f
        JOIN stocks.assets a ON f.asset_id = a.asset_id
        WHERE f.user_id = %s
        ORDER BY a.canonical_symbol
        """,
        (user_id,),
    )
    rows = [r[0] for r in cur.fetchall()]
    conn.close()
    return rows
