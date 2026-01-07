-- init_stocks.sql
CREATE SCHEMA IF NOT EXISTS stocks;

CREATE TABLE IF NOT EXISTS stock_prices (
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