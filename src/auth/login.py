from data.db_connection import get_connection
from .password import verify_password
from .logger import log_event
from .security import is_account_locked, register_failed_login
from .token import create_token


def login_user(email: str, password: str):
    """
    Loggt einen Benutzer per Email + Passwort ein.
    Rückgabe: dict mit {success: bool, token: str|None, error: str|None}
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Nutzer suchen
        cursor.execute("""
            SELECT id, password_hash, deleted_at, locked_until, failed_login_attempts
            FROM auth.users
            WHERE email = %s
        """, (email,))
        row = cursor.fetchone()

        if not row:
            # Kein Nutzer gefunden → Event loggen ohne user_id
            log_event(conn, None, "login_failed")
            return {"success": False, "error": "invalid_credentials"}

        user_id, pw_hash, deleted_at, locked_until, failed_attempts = row
        user = {
            "id": user_id,
            "password_hash": pw_hash,
            "deleted_at": deleted_at,
            "locked_until": locked_until,
            "failed_login_attempts": failed_attempts
        }

        # Account gelöscht?
        if deleted_at is not None:
            log_event(conn, user_id, "login_failed")
            return {"success": False, "error": "account_deleted"}

        # Account gesperrt?
        if is_account_locked(user):
            log_event(conn, user_id, "login_failed")
            return {"success": False, "error": "account_locked"}

        # Passwort prüfen
        if not verify_password(password, pw_hash):
            register_failed_login(user_id, conn)
            log_event(conn, user_id, "login_failed")
            return {"success": False, "error": "invalid_credentials"}

        # Erfolgreiches Login → fehlgeschlagene Versuche resetten
        cursor.execute("""
            UPDATE auth.users
            SET failed_login_attempts = 0, locked_until = NULL
            WHERE id = %s
        """, (user_id,))
        conn.commit()

        # Token erzeugen
        token = create_token(user_id)

        # Login Event loggen
        log_event(conn, user_id, "login_success")

        return {"success": True, "token": token}

    finally:
        cursor.close()
        conn.close()
