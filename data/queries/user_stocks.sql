-- 2️⃣ Alle vorhandenen Symbole aus stock_prices einfügen
INSERT INTO stocks.symbols (symbol)
SELECT DISTINCT symbol
FROM stocks.stock_prices
ON CONFLICT (symbol) DO NOTHING;

-- 3️⃣ Favoriten für User ID 1 einfügen
INSERT INTO stocks.favorites (user_id, symbol)
SELECT 1, symbol
FROM stocks.symbols
LIMIT 3
ON CONFLICT (user_id, symbol) DO NOTHING;