-- init_auth.sql
CREATE SCHEMA IF NOT EXISTS auth;

CREATE TABLE IF NOT EXISTS auth.users (
    id SERIAL PRIMARY KEY,

    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,

    first_name TEXT,
    last_name TEXT,

    street TEXT,
    postal TEXT,
    city TEXT,
    country TEXT,

    failed_login_attempts INT DEFAULT 0,
    locked_until TIMESTAMP NULL,

    deleted_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE auth.login_events (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES auth.users(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL, -- login_success, login_failed, register, lock
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON auth.users(email);
CREATE INDEX idx_login_user ON auth.login_events(user_id);