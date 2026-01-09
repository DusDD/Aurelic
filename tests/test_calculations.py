from src.stocks.calculations import calculate_top_movers

def test_top_movers_basic():
    price_data = {
        "AAPL": [("2026-01-05", 150), ("2026-01-04", 100)],
        "AMZN": [("2026-01-05", 200), ("2026-01-04", 100)],
        "GOOG": [("2026-01-05", 120), ("2026-01-04", 100)],
    }
    result = calculate_top_movers(price_data, top_n=2)
    assert result[0][0] == "AMZN"
    assert round(result[0][1], 2) == 100.0
    assert result[1][0] == "AAPL"
    assert round(result[1][1], 2) == 50.0
