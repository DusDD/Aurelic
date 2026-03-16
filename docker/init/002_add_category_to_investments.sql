BEGIN;

ALTER TABLE stocks.investments
ADD COLUMN IF NOT EXISTS category TEXT;

ALTER TABLE stocks.investments
ALTER COLUMN category SET DEFAULT 'stock';

UPDATE stocks.investments i
SET category = COALESCE(a.category, 'stock')
FROM stocks.assets a
WHERE a.asset_id = i.asset_id
  AND i.category IS NULL;

ALTER TABLE stocks.investments
ALTER COLUMN category SET NOT NULL;

ALTER TABLE stocks.investments
DROP CONSTRAINT IF EXISTS investments_category_check;

ALTER TABLE stocks.investments
ADD CONSTRAINT investments_category_check
CHECK (category IN ('stock','etf','crypto','commodity','index'));

CREATE INDEX IF NOT EXISTS idx_investments_user_category
ON stocks.investments(user_id, category);

COMMIT;