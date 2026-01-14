SYMBOLS = {
    "yfinance": [
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
    ],

# _____________________________________________________________________________
# POLYGON

    "polygon": [
        # bestehende Aktien
        {"symbol": "AAPL", "category": "stock"},
        {"symbol": "AMZN", "category": "stock"},
        {"symbol": "MSFT", "category": "stock"},
        {"symbol": "TSLA", "category": "stock"},

        # neue Aktien
        {"symbol": "NVDA", "category": "stock"},
        {"symbol": "MRNA", "category": "stock"},
        {"symbol": "UL", "category": "stock"},               # Unilever (NYSE)

#        {"symbol": "XETRA:VOW3", "category": "stock"},       # Volkswagen
#        {"symbol": "XETRA:RHM", "category": "stock"},        # Rheinmetall
#        {"symbol": "XETRA:BMW", "category": "stock"},        # BMW
#        {"symbol": "XETRA:BAYN", "category": "stock"},       # Bayer
#        {"symbol": "XETRA:BAS", "category": "stock"},        # BASF

#        {"symbol": "LSE:AML", "category": "stock"},          # Aston Martin
#        {"symbol": "XETRA:MBG", "category": "stock"},        # Mercedes-Benz
#        {"symbol": "LSE:CWR", "category": "stock"},          # Ceres Power
#        {"symbol": "XETRA:SHA", "category": "stock"},        # Schaeffler
        {"symbol": "MNST", "category": "stock"},             # Monster Beverage

        # neue Indizes/ETFs
        {"symbol": "URTH", "category": "etf"},
        {"symbol": "SPY", "category": "etf"},
#        {"symbol": "I:SPX", "category": "index"},            # S&P500

        # Kryptowährungen
        {"symbol": "X:BTCUSD", "category": "crypto"},
        {"symbol": "X:SOLUSD", "category": "crypto"},
        {"symbol": "X:DOGEUSD", "category": "crypto"},

        # Rohstoffe
        {"symbol": "C:XAUUSD", "category": "commodity"},     # Gold
        {"symbol": "C:XAGUSD", "category": "commodity"},     # Silber

        # Sonderfälle: Porsche auf Xetra
#        {"symbol": "XETRA:P911", "category": "stock"},
    ]
}