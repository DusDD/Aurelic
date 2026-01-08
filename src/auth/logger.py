def log_event(conn, user_id: int | None, event_type: str):
    """
    Speichert ein Login-/Register-Event.
    user_id: int oder None
    event_type: 'login_success', 'login_failed', 'register', 'lock'
    """
    with conn.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO auth.login_events (user_id, event_type)
            VALUES (%s, %s)
            """,
            (user_id, event_type)
        )
    conn.commit()
