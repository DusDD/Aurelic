from data.db_connection import get_connection
from .security import (
    verify_password,
    is_account_locked,
    register_failed_attempt,
    reset_failed_attempts
)
from .logger import log_event


def login_user(username: str, password: str) -> dict:
    """
    Rückgabe:
    {
        "success": bool,
        "user_id": int | None,
        "error": str | None
    }
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, password_hash, failed_attempts, locked_until
        FROM auth.users
        WHERE username = %s
        """,
        (username,)
    )

    row = cursor.fetchone()

    if row is None:
        log_event(conn, None, "login_failed")
        conn.close()
        return {"success": False, "user_id": None, "error": "invalid_credentials"}

    user = {
        "id": row[0],
        "password_hash": row[1],
        "failed_attempts": row[2],
        "locked_until": row[3]
    }

    # Account gesperrt?
    if is_account_locked(user):
        log_event(conn, user["id"], "account_locked")
        conn.close()
        return {"success": False, "user_id": None, "error": "account_locked"}

    # Passwort prüfen
    if not verify_password(password, user["password_hash"]):
        user = register_failed_attempt(user)

        cursor.execute(
            """
            UPDATE auth.users
            SET failed_attempts = %s, locked_until = %s
            WHERE id = %s
            """,
            (user["failed_attempts"], user["locked_until"], user["id"])
        )
        conn.commit()

        log_event(conn, user["id"], "login_failed")
        conn.close()
        return {"success": False, "user_id": None, "error": "invalid_credentials"}

    # Login erfolgreich
    user = reset_failed_attempts(user)
    cursor.execute(
        """
        UPDATE auth.users
        SET failed_attempts = 0, locked_until = NULL
        WHERE id = %s
        """,
        (user["id"],)
    )
    conn.commit()

    log_event(conn, user["id"], "login_success")
    conn.close()

    return {"success": True, "user_id": user["id"], "error": None}
