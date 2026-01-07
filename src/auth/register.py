from data.db_get_connection import get_connection
from .security import hash_password
from .logger import log_event


def register_user(username: str, password: str):
    conn = get_connection()
    cursor = conn.cursor()

    # Hash des Passworts erstellen
    password_hashed = hash_password(password)

    try:
        cursor.execute(
            "INSERT INTO auth.users (username, password_hash) VALUES (%s, %s) RETURNING id",
            (username, password_hashed)
        )
        user_id = cursor.fetchone()[0]
        conn.commit()

        # Loggen des Events
        log_event(user_id, "register", conn)

        return user_id
    except Exception as e:
        conn.rollback()
        if "unique constraint" in str(e).lower():
            raise ValueError("Username already exists")
        else:
            raise
    finally:
        cursor.close()
        conn.close()