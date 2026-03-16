-- 001_create_investments.sql
-- Postgres Migration: Investments pro User pro Asset
-- Schema-Style passend zu: stocks.prices, stocks.stock_intraday, stocks.favorites
-- Voraussetzung: schemas "stocks" und "auth" existieren, sowie auth.users(id) und stocks.assets(asset_id)

BEGIN;

-- Table: stocks.investments
CREATE TABLE IF NOT EXISTS stocks.investments (
    user_id    INT NOT NULL,
    asset_id   INT NOT NULL REFERENCES stocks.assets(asset_id) ON DELETE CASCADE,

    -- Position / Bestand
    quantity   NUMERIC(20, 8) NOT NULL DEFAULT 0 CHECK (quantity >= 0),

    -- Optional (für später, kann leer bleiben)
    avg_cost   NUMERIC(20, 8),
    currency   TEXT,
    note       TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    PRIMARY KEY (user_id, asset_id),
    FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_investments_user  ON stocks.investments(user_id);
CREATE INDEX IF NOT EXISTS idx_investments_asset ON stocks.investments(asset_id);

-- Trigger function for updated_at
CREATE OR REPLACE FUNCTION stocks.set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger: auto-update updated_at on row updates
DROP TRIGGER IF EXISTS trg_investments_updated_at ON stocks.investments;

CREATE TRIGGER trg_investments_updated_at
BEFORE UPDATE ON stocks.investments
FOR EACH ROW
EXECUTE FUNCTION stocks.set_updated_at();

COMMIT;