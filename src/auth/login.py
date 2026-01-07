from data.db_connection import get_connection
from .security import (
    verify_password,
    is_account_locked
)
from .logger import log_event
from .token import create_token
from .security import register_failed_login


def login_user(username: str, password: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, password_hash, deleted_at, locked_until
        FROM auth.users
        WHERE username = %s
    """, (username,))
    row = cursor.fetchone()

    if not row:
        return {"success": False, "error": "invalid_credentials"}

    user_id, pw_hash, deleted_at, locked_until = row
    user = {
        "id": user_id,
        "password_hash": pw_hash,
        "deleted_at": deleted_at,
        "locked_until": locked_until
    }

    if deleted_at is not None:
        return {"success": False, "error": "account_deleted"}

    if is_account_locked(user):
        return {"success": False, "error": "account_locked"}

    if not verify_password(password, pw_hash):
        register_failed_login(user_id, conn)
        return {"success": False, "error": "invalid_credentials"}

    # Erfolg → Reset
    cursor.execute("""
        UPDATE auth.users
        SET failed_login_attempts = 0, locked_until = NULL
        WHERE id = %s
    """, (user_id,))
    conn.commit()

    token = create_token(user_id)
    return {"success": True, "token": token}
