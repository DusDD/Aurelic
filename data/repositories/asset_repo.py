from data.db_connection import get_connection

def get_assets_for_provider(provider):
    """
    Liefert:
    [
      {asset_id:1, provider_symbol:"AAPL"},
      ...
    ]
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT a.asset_id, s.provider_symbol
        FROM stocks.assets a
        JOIN stocks.asset_symbols s
          ON a.asset_id = s.asset_id
        WHERE s.provider = %s
          AND a.active = true
    """, (provider,))

    rows = cur.fetchall()
    conn.close()

    return [{"asset_id":r[0], "symbol":r[1]} for r in rows]
