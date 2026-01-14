SELECT DISTINCT date, source
FROM stocks.prices
ORDER BY date DESC
LIMIT 10;

SELECT DISTINCT ON (asset_id, date)
*
FROM stocks.prices
ORDER BY asset_id, date, quality_score DESC;

-- broken
SELECT 1
FROM stocks.prices
WHERE asset_id = 1
AND date = '2026-01-03'
AND source='yahoo';

SELECT *
FROM stocks.stock_intraday
LIMIT 10;

SELECT *
FROM stocks.prices
WHERE asset_id = 4
AND open = 435.9
ORDER BY date
LIMIT 10;

SELECT *
FROM stocks.stock_intraday
ORDER BY datetime DESC
LIMIT 10;