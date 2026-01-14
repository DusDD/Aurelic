# tests/test_db_calls.py
from src.stocks import db_calls
from src.auth.token import create_token

# --- Setup: Test-Token ---
# Angenommen, User-ID 1 existiert in auth.users
TEST_USER_ID = 1
test_token = create_token(TEST_USER_ID)

def print_top_movers_overall():
    print("=== Top Movers Overall ===")
    movers = db_calls.get_top_movers_overall(test_token, limit=5)
    for sym, close, prev, pct in movers:
        print(f"{sym}: {prev} -> {close} ({pct}%)")

def print_top_movers_favorites():
    print("=== Top Movers Favorites ===")
    movers = db_calls.get_top_movers_favorites(test_token, limit=5)
    for sym, close, prev, pct in movers:
        print(f"{sym}: {prev} -> {close} ({pct}%)")

def print_stock_prices(symbol):
    print(f"=== Stock Prices: {symbol} ===")
    prices = db_calls.get_stock_prices(test_token, symbol)
    for date, o, h, l, c, v in prices[:5]:  # nur die letzten 5
        print(f"{date} | O:{o} H:{h} L:{l} C:{c} V:{v}")

def print_symbols():
    print("=== All Symbols ===")
    symbols = db_calls.get_all_symbols(test_token)
    for s in symbols[:10]:
        print(s)

def print_favorites():
    print("=== User Favorites ===")
    favs = db_calls.get_user_favorites(test_token)
    print(favs)

if __name__ == "__main__":
    print_symbols()
    print_favorites()
    print_top_movers_overall()
    print_top_movers_favorites()
    print_stock_prices("AAPL")  # Beispielsymbol
