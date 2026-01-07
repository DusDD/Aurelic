-- Alle Sources aus stock_prices
SELECT DISTINCT source
FROM stocks.stock_prices
ORDER BY source;

-- Alle SYMBOLS aus stock_prices
SELECT DISTINCT symbol
FROM stocks.stock_prices
ORDER BY symbol;