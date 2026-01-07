from auth.login import login_user
from data.db_call import get_stock_prices
from src.auth.register import register_user

register = register_user("sky", "sky123")
login = login_user("sky", "sky123")

if login["success"]:
    token = login["token"]
    prices = get_stock_prices(token, "AAPL")
    print(prices[:5])
else:
    print("Login failed:", login["error"])