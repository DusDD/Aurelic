def log_event(user_id: int, event_type: str, conn):
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO auth.login_events (user_id, event_type) VALUES (%s, %s)",
        (user_id, event_type)
    )
    conn.commit()
    cursor.close()
