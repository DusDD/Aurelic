import requests
import requests
import time

API_KEY = ""

# INPUT
INPUT_LIST = [
    ('AAPL','Apple','stock'),
    ('AMZN','Amazon','stock'),
    ('MSFT','Microsoft','stock'),
    ('TSLA','Tesla','stock'),
    ('NVDA','Nvidia','stock'),
    ('MRNA','Moderna','stock'),
    ('UL','Unilever','stock'),
    ('BMW','BMW','stock'),
    ('VOW3','Volkswagen','stock'),
    ('RHM','Rheinmetall','stock'),
    ('BAYN','Bayer','stock'),
    ('BAS','BASF','stock'),
    ('AML','Aston Martin','stock'),
    ('MBG','Mercedes-Benz','stock'),
    ('CWR','Ceres Power','stock'),
    ('SHA','Schaeffler','stock'),
    ('MNST','Monster Beverage','stock'),
    ('URTH','iShares MSCI World ETF','etf'),
    ('SPY','SPDR S&P 500 ETF','etf'),
    ('SPX','S&P 500 Index','index'),
    ('BTC','Bitcoin','crypto'),
    ('SOL','Solana','crypto'),
    ('DOGE','Dogecoin','crypto'),
    ('XAU','Gold','commodity'),
    ('XAG','Silver','commodity'),
    ('P911','Porsche AG','stock')
]

# MAPPING-LOGIK
def build_polygon_ticker(symbol, asset_type):
    us_stocks = ['AAPL','AMZN','MSFT','TSLA','NVDA','MRNA','UL','MNST']
    nasdaq = ['AAPL','AMZN','MSFT','TSLA','NVDA','MRNA','MNST']
    nyse = ['UL']
    etfs = ['URTH','SPY']

    if asset_type == "stock":
        if symbol in nasdaq:
            return symbol, "NASDAQ"
        elif symbol in nyse:
            return symbol, "NYSE"
        else:
            return f"XETRA:{symbol}", "XETRA"

    if asset_type == "etf":
        return symbol, "NYSEARCA"

    if asset_type == "index":
        return f"I:{symbol}", "INDEX"

    if asset_type == "crypto":
        return f"X:{symbol}USD", "CRYPTO"

    if asset_type == "commodity":
        return f"C:{symbol}USD", "COMMODITY"

    return None, None


# POLYGON CALL
def fetch_polygon_reference(ticker, retries=3):
    url = f"https://api.polygon.io/v3/reference/tickers/{ticker}"
    params = {"apiKey": API_KEY}

    for i in range(retries):
        r = requests.get(url, params=params)

        if r.status_code == 200:
            return r.json()

        elif r.status_code == 429:
            print(f"⚠ Rate limit für {ticker} – warte 10s...")
            time.sleep(10)

        else:
            print(f"❌ Fehler {r.status_code} für {ticker}")
            return None

    print(f"❌ Abbruch für {ticker}")
    return None


# MAIN
def build_result_dict():
    result = {}
    counter = 1

    for symbol, name, asset_type in INPUT_LIST:
        polygon_ticker, exchange = build_polygon_ticker(symbol, asset_type)

        api_result = fetch_polygon_reference(polygon_ticker)

        result[counter] = (
            counter,
            "polygon",
            polygon_ticker,
            exchange
        )

        counter += 1

    return result


if __name__ == "__main__":
    data = build_result_dict()

    print("\n--- RESULT ---")
    for k,v in data.items():
        print(v)
