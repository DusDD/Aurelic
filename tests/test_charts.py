from src.stocks import charts

# USAGE
# execute "pytest tests/test_charts.py" in project root

# -----------------------------
# Mock für DB-Call
# -----------------------------
def mock_get_stock_prices(token, symbol):
    return [
        # neuestes zuerst (wie aus DB)
        ("2026-01-05", 270.64, 271.51, 266.14, 267.26, 45633196),
        ("2026-01-02", 272.255, 277.84, 269, 271.01, 37791773),
        ("2025-12-31", 273.06, 273.68, 271.75, 271.86, 27258874),
    ]


# -----------------------------
# Price Timeseries
# -----------------------------
def test_get_price_timeseries(monkeypatch):
    monkeypatch.setattr(
        charts,
        "get_stock_prices",
        mock_get_stock_prices
    )

    result = charts.get_price_timeseries("fake-token", "AAPL")

    assert result["symbol"] == "AAPL"
    assert len(result["dates"]) == 3

    # Chronologisch!
    assert result["dates"][0] == "2025-12-31"
    assert result["dates"][-1] == "2026-01-05"

    assert result["closes"][-1] == 267.26
    assert result["opens"][0] == 273.06
    assert result["volumes"][-1] == 45633196


# -----------------------------
# Candlestick
# -----------------------------
def test_get_candlestick_data(monkeypatch):
    monkeypatch.setattr(
        charts,
        "get_stock_prices",
        mock_get_stock_prices
    )

    result = charts.get_candlestick_data("fake-token", "AAPL")

    assert result["symbol"] == "AAPL"
    assert len(result["data"]) == 3

    first = result["data"][0]  # ältester

    assert first["date"] == "2025-12-31"
    assert first["open"] == 273.06
    assert first["high"] == 273.68
    assert first["low"] == 271.75
    assert first["close"] == 271.86
