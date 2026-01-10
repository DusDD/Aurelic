SYMBOLS = [
    # bestehende Aktien
    {"symbol": "AAPL", "category": "stock"},
    {"symbol": "AMZN", "category": "stock"},
    {"symbol": "MSFT", "category": "stock"},
    {"symbol": "TSLA", "category": "stock"},

    # neue Aktien
    {"symbol": "NVDA", "category": "stock"},
    {"symbol": "MRNA", "category": "stock"},
    {"symbol": "UL", "category": "stock"},
    {"symbol": "VOW3.DE", "category": "stock"},
    {"symbol": "RHM.DE", "category": "stock"},
    {"symbol": "BMW.DE", "category": "stock"},
    {"symbol": "BAYN.DE", "category": "stock"},
    {"symbol": "BAS.DE", "category": "stock"},
    {"symbol": "AML.L", "category": "stock"},
    {"symbol": "MBG.DE", "category": "stock"},
    {"symbol": "CWR.L", "category": "stock"},
    {"symbol": "SHA.DE", "category": "stock"},
    {"symbol": "MNST", "category": "stock"},
    # neue Indizes/ETFs
    {"symbol": "URTH", "category": "etf"},
    {"symbol": "SPY", "category": "etf"},
    {"symbol": "^GSPC", "category": "index"},
    # Kryptowährungen
    {"symbol": "BTC", "category": "crypto"},
    {"symbol": "SOL", "category": "crypto"},
    {"symbol": "DOGE", "category": "crypto"},
    # Rohstoffe
    {"symbol": "XAU", "category": "commodity"},  # Gold
    {"symbol": "XAG", "category": "commodity"},  # Silber
    # Sonderfälle: Porsche auf Xetra
    {"symbol": "P911.DE", "category": "stock"},
]

MISSING = [
    {"symbol": "DOGE", "category": "crypto"},
    {"symbol": "AAPL", "category": "stock"},
    {"symbol": "SHA.DE", "category": "stock"},
]