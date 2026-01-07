def log_event(conn, user_id: int | None, event_type: str):
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO auth.login_events (user_id, event_type)
        VALUES (%s, %s)
        """,
        (user_id, event_type)
    )
    conn.commit()
    cursor.close()
