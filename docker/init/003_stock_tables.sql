-- historical
CREATE TABLE stocks.prices (
    asset_id INT REFERENCES stocks.assets(asset_id) ON DELETE CASCADE,
    date DATE NOT NULL,

    open NUMERIC,
    high NUMERIC,
    low NUMERIC,
    close NUMERIC,
    volume BIGINT,

    source TEXT,
    quality_score INT,

    PRIMARY KEY (asset_id, date, source)
);

CREATE INDEX idx_prices_asset ON stocks.prices(asset_id);
CREATE INDEX idx_prices_date ON stocks.prices(date);

-- intraday
CREATE TABLE stocks.stock_intraday (
    asset_id INT REFERENCES stocks.assets(asset_id) ON DELETE CASCADE,
    datetime TIMESTAMP NOT NULL,

    open NUMERIC,
    high NUMERIC,
    low NUMERIC,
    close NUMERIC,
    volume BIGINT,

    interval TEXT,
    source TEXT,

    PRIMARY KEY(asset_id, datetime, interval)
);

CREATE TABLE stocks.favorites (
    user_id INT NOT NULL,
    asset_id INT REFERENCES stocks.assets(asset_id),

    PRIMARY KEY(user_id, asset_id),
    FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE
);
