from data.db_connection import get_connection
from .logger import log_event

def delete_user(email: str) -> dict:
    """
    Soft-Delete: Markiert einen Benutzer als gelöscht (deleted_at),
    statt ihn aus der Datenbank zu entfernen.
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Prüfen, ob Benutzer existiert und noch nicht gelöscht
        cursor.execute(
            "SELECT id, deleted_at FROM auth.users WHERE email = %s",
            (email,)
        )
        row = cursor.fetchone()

        if row is None:
            return {"success": False, "user_id": None, "error": "user_not_found"}

        user_id, deleted_at = row

        if deleted_at is not None:
            return {"success": False, "user_id": user_id, "error": "user_already_deleted"}

        # Soft-Delete durchführen
        cursor.execute(
            "UPDATE auth.users SET deleted_at = NOW() WHERE id = %s",
            (user_id,)
        )
        conn.commit()

        # Logging
        log_event(conn, user_id, "soft_delete_user")

        return {"success": True, "user_id": user_id, "error": None}

    finally:
        cursor.close()
        conn.close()
