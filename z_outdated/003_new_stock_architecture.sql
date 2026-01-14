CREATE TABLE IF NOT EXISTS stocks.assets (
    asset_id SERIAL PRIMARY KEY,
    canonical_symbol TEXT UNIQUE NOT NULL, -- z.B. AAPL, BMW
    name TEXT,
    category TEXT CHECK (category IN ('stock','etf','crypto','commodity','index')),
    isin TEXT,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS stocks.asset_symbols (
    id SERIAL PRIMARY KEY,
    asset_id INT REFERENCES stocks.assets(asset_id) ON DELETE CASCADE,

    provider TEXT NOT NULL, -- 'yahoo','polygon'
    provider_symbol TEXT NOT NULL,

    exchange TEXT,
    UNIQUE(provider, provider_symbol)
);

CREATE TABLE IF NOT EXISTS stocks.prices (
    asset_id INT REFERENCES stocks.assets(asset_id) ON DELETE CASCADE,
    date DATE NOT NULL,

    open NUMERIC,
    high NUMERIC,
    low NUMERIC,
    close NUMERIC,
    volume BIGINT,

    source TEXT, -- yahoo, polygon
    quality_score INT, -- optional (polygon = 100, yahoo = 50)

    PRIMARY KEY (asset_id, date, source)
);

