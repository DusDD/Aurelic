CREATE TABLE IF NOT EXISTS notes (
  id            BIGSERIAL PRIMARY KEY,
  user_id       BIGINT NOT NULL,
  asset_id      BIGINT,
  symbol        TEXT,
  title         TEXT,
  body          TEXT NOT NULL,
  tags          TEXT,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_notes_user
  ON notes(user_id, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_notes_user_asset
  ON notes(user_id, asset_id, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_notes_user_symbol
  ON notes(user_id, symbol, updated_at DESC);