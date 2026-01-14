CREATE SCHEMA IF NOT EXISTS stocks;

-- =================================
-- ASSETS (kanonisch)
-- =================================
CREATE TABLE IF NOT EXISTS stocks.assets (
    asset_id SERIAL PRIMARY KEY,
    canonical_symbol TEXT UNIQUE NOT NULL,
    name TEXT,
    category TEXT CHECK (
        category IN ('stock','etf','crypto','commodity','index')
    ),
    isin TEXT,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =================================
-- PROVIDER SYMBOLS
-- =================================
CREATE TABLE IF NOT EXISTS stocks.asset_symbols (
    id SERIAL PRIMARY KEY,
    asset_id INT REFERENCES stocks.assets(asset_id) ON DELETE CASCADE,

    provider TEXT NOT NULL, -- yahoo, polygon
    provider_symbol TEXT NOT NULL,
    exchange TEXT,

    UNIQUE(provider, provider_symbol)
);
