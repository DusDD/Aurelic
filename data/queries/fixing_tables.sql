SELECT COUNT(*)
FROM stocks.stock_intraday
WHERE asset_id IS NULL;

SELECT symbol, COUNT(*)
FROM stocks.stock_intraday
WHERE asset_id IS NULL
GROUP BY symbol;

UPDATE stocks.asset_symbols
SET provider_symbol = 'NVDA'
WHERE provider_symbol = 'MVDA'
AND provider = 'polygon';
