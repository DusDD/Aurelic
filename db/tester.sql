CREATE TABLE IF NOT EXISTS tester_stocks (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(100),
    price NUMERIC(10, 2),
    last_updated TIMESTAMP DEFAULT NOW()
);

SELECT * FROM tester_stocks;

--this is bash script:

\dt                 --shows all tables
\d tester_stocks    --shows table tester_stocks

-- ============================================
--  Testdaten für Tabelle: tester_stocks
--  Beschreibung: Beispielhafte Aktienwerte
--  ============================================

-- Optional: Tabelle leeren, falls schon Daten vorhanden sind
TRUNCATE TABLE stocks RESTART IDENTITY;

-- Beispiel-Datensätze einfügen
INSERT INTO tester_stocks (ticker, name, price)
VALUES
    ('AAPL', 'Apple Inc.', 190.45),
    ('GOOGL', 'Alphabet Inc.', 138.77),
    ('AMZN', 'Amazon.com Inc.', 124.33),
    ('MSFT', 'Microsoft Corporation', 330.12),
    ('TSLA', 'Tesla Inc.', 256.89),
    ('NVDA', 'NVIDIA Corporation', 472.51),
    ('META', 'Meta Platforms Inc.', 305.21),
    ('NFLX', 'Netflix Inc.', 402.44),
    ('BABA', 'Alibaba Group Holding Ltd.', 88.56),
    ('SAP', 'SAP SE', 145.37);

-- Überprüfen, ob Daten korrekt eingefügt wurden
SELECT * FROM stocks;