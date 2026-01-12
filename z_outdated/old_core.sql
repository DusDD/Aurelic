-- 001_schema_and_core.sql
CREATE SCHEMA IF NOT EXISTS stocks;

-- Existing stock_prices table
CREATE TABLE IF NOT EXISTS stocks.stock_prices (
    symbol TEXT NOT NULL,
    date DATE NOT NULL,
    open NUMERIC,
    high NUMERIC,
    low NUMERIC,
    close NUMERIC,
    volume BIGINT,
    source TEXT,
    PRIMARY KEY (symbol, date)
);

-- Indexe für Performance
CREATE INDEX IF NOT EXISTS idx_stock_prices_symbol ON stocks.stock_prices(symbol);
CREATE INDEX IF NOT EXISTS idx_stock_prices_date ON stocks.stock_prices(date);

-- Symbols table
CREATE TABLE IF NOT EXISTS stocks.symbols (
    symbol TEXT PRIMARY KEY,
    name TEXT,
    category TEXT CHECK (category IN ('stock','etf','crypto','commodity')),
    exchange TEXT,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS stocks.stock_intraday (
    symbol TEXT REFERENCES stocks.symbols(symbol),
    datetime TIMESTAMP,
    open NUMERIC,
    high NUMERIC,
    low NUMERIC,
    close NUMERIC,
    volume BIGINT,
    interval TEXT, -- '1min','5min','15min'
    source TEXT,
    PRIMARY KEY (symbol, datetime, interval)
);

-- Favorites per user
CREATE TABLE IF NOT EXISTS stocks.favorites (
    user_id INT NOT NULL,
    symbol TEXT NOT NULL REFERENCES stocks.symbols(symbol),
    PRIMARY KEY (user_id, symbol),
    FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE
);

-- Optional: Top movers cache
CREATE TABLE IF NOT EXISTS stocks.top_movers (
    symbol TEXT REFERENCES stocks.symbols(symbol),
    date DATE NOT NULL,
    pct_change NUMERIC,
    rank_overall INT,
    rank_favorites INT,
    PRIMARY KEY (symbol, date)
);

-- alte Architektur erweitern
INSERT INTO stocks.assets (canonical_symbol, name, category)
SELECT DISTINCT symbol, name, category
FROM stocks.symbols;

INSERT INTO stocks.asset_symbols (asset_id, provider, provider_symbol)
SELECT a.asset_id, 'yahoo', s.symbol
FROM stocks.assets a
JOIN stocks.symbols s
ON a.canonical_symbol = s.symbol;

-- Beispiel
INSERT INTO stocks.asset_symbols (asset_id, provider, provider_symbol)
VALUES
(01,'polygon','XETRA:BMW'),
(02,'polygon','AAPL'),
(03,'polygon','AMZN'),
(04,'polygon','MSFT'),
(05,'polygon','TSLA'),
(06,'polygon','MVDA'),
(07,'polygon','MRNA'),
(08,'polygon','UL'),
(09,'polygon','XETRA:VOW3'),
(10,'polygon','XETRA:RHM'),
(11,'polygon','XETRA:BAYN'),
(12,'polygon','XETRA:BAS'),
(13,'polygon','LSE:AML'),
(14,'polygon','XETRA:MBG'),
(15,'polygon','LSE:CWR'),
(16,'polygon','XETRA:SHA'),
(17,'polygon','MNST'),
(18,'polygon','URTH'),
(19,'polygon','SPY'),
(20,'polygon','I:SPX'),
(21,'polygon','X:BTCUSD'),
(22,'polygon','X:SOLUSD'),
(23,'polygon','X:DOGEUSD'),
(24,'polygon','C:XAUUSD'),
(25,'polygon','C:XAGUSD'),
(26,'polygon','XETRA:P911');


INSERT INTO stocks.prices
(asset_id, date, open, high, low, close, volume, source, quality_score)
SELECT
    a.asset_id,
    p.date,
    p.open,
    p.high,
    p.low,
    p.close,
    p.volume,
    p.source,
    CASE
        WHEN p.source='polygon' THEN 100
        ELSE 50
    END
FROM stocks.stock_prices p
JOIN stocks.assets a
ON a.canonical_symbol = p.symbol;

-- intraday table an neue Architektur anpassen
ALTER TABLE stocks.stock_intraday
ADD COLUMN asset_id INT REFERENCES stocks.assets(asset_id);

UPDATE stocks.stock_intraday i
SET asset_id = a.asset_id
FROM stocks.asset_symbols s
JOIN stocks.assets a ON a.asset_id=s.asset_id
WHERE i.symbol=s.provider_symbol
AND s.provider='polygon';

ALTER TABLE stocks.stock_intraday
DROP CONSTRAINT stock_intraday_pkey;

ALTER TABLE stocks.stock_intraday
ADD PRIMARY KEY(asset_id,datetime,interval);

UPDATE stocks.stock_intraday i
SET asset_id = a.asset_id
FROM stocks.asset_symbols s
JOIN stocks.assets a ON a.asset_id = s.asset_id
WHERE i.asset_id IS NULL
AND i.symbol = s.provider_symbol
AND s.provider = 'polygon';

SELECT COUNT(*)
FROM stocks.stock_intraday
WHERE asset_id IS NULL;