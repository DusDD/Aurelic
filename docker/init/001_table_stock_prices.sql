-- 001_table_stock_prices.sql
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
