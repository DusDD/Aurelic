from data.db_connection import get_connection
from .password import validate_password, hash_password
from .logger import log_event


def register_user(
    first_name,
    last_name,
    email,
    password,
    street="",
    postal="",
    city="",
    country=""
):
    """
    Registriert einen neuen Nutzer.
    Rückgabe:
    {
        success: bool,
        user_id: int | None,
        error: str | None
    }
    """

    # 1) Passwort validieren
    valid, error_code = validate_password(password)
    if not valid:
        return {"success": False, "user_id": None, "error": error_code}

    conn = get_connection()
    cursor = conn.cursor()

    # 2) Prüfen ob Email existiert
    cursor.execute(
        "SELECT id FROM auth.users WHERE email = %s",
        (email,)
    )
    if cursor.fetchone():
        cursor.close()
        conn.close()
        return {"success": False, "user_id": None, "error": "email_taken"}

    # 3) Passwort hashen
    hashed_pw = hash_password(password)

    # 4) User speichern
    cursor.execute("""
        INSERT INTO auth.users
        (
            first_name,
            last_name,
            email,
            password_hash,
            street,
            postal_code,
            city,
            country
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        RETURNING id
    """, (
        first_name,
        last_name,
        email,
        hashed_pw,
        street,
        postal,
        city,
        country
    ))

    user_id = cursor.fetchone()[0]
    conn.commit()

    # 5) Logging
    log_event(conn, user_id, "register")

    cursor.close()
    conn.close()

    return {"success": True, "user_id": user_id, "error": None}
