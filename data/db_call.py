import psycopg2
from psycopg2.extras import RealDictCursor
from data.db_get_connection import get_connection

get_connection()

def init_auth_schema(conn):
    """Optional: Erstinitialisierung des auth Schemas"""
    with conn.cursor() as cur:
        cur.execute("""
        CREATE SCHEMA IF NOT EXISTS auth;
        CREATE TABLE IF NOT EXISTS auth.users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            failed_attempts INT DEFAULT 0,
            locked_until TIMESTAMP NULL
        );
        CREATE TABLE IF NOT EXISTS auth.login_events (
            id SERIAL PRIMARY KEY,
            user_id INT REFERENCES auth.users(id),
            event_type TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        conn.commit()