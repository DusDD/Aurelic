# data/db_calls.py
from data.db_connection import get_connection
from src.auth.guard import require_auth
from src.stocks.calculations import calculate_top_movers

def get_top_movers_overall(token: str, top_n: int = 3):
    user_id = require_auth(token)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT symbol, date, close FROM stocks.stock_prices ORDER BY date DESC")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    # Konvertiere DB-Ergebnis in price_data dict
    price_data = {}
    for symbol, date, close in rows:
        price_data.setdefault(symbol, []).append((date, float(close)))

    return calculate_top_movers(price_data, top_n)
