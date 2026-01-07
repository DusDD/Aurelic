from .security import validate_password
from data.db_connection import get_connection
from .logger import log_event
from passlib.hash import bcrypt

def register_user(username: str, password: str) -> dict:
    """
    Registriert einen neuen Nutzer. Gibt ein Dict zurück:
    {success: bool, user_id: int | None, error: str | None}
    """

    # Passwort validieren
    valid, error_code = validate_password(password)
    if not valid:
        return {"success": False, "user_id": None, "error": error_code}

    conn = get_connection()
    cursor = conn.cursor()

    # Prüfen, ob Benutzer existiert
    cursor.execute("SELECT id FROM auth.users WHERE username = %s", (username,))
    if cursor.fetchone() is not None:
        conn.close()
        return {"success": False, "user_id": None, "error": "username_taken"}

    # Passwort hashen
    # Passwort in UTF-8 konvertieren und max 72 Bytes nehmen
    password_bytes = password.encode("utf-8")[:72]
    hashed_pw = bcrypt.hash(password_bytes)

    # Benutzer erstellen
    cursor.execute(
        "INSERT INTO auth.users (username, password_hash) VALUES (%s, %s) RETURNING id",
        (username, hashed_pw)
    )
    user_id = cursor.fetchone()[0]
    conn.commit()

    # Logging
    log_event(conn, user_id, "register")

    cursor.close()
    conn.close()

    return {"success": True, "user_id": user_id, "error": None}
