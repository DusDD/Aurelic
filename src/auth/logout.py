from data.db_connection import get_connection


def revoke_token(token: str):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO auth.revoked_tokens (token)
        VALUES (%s)
    """, (token,))

    conn.commit()
    cur.close()
    conn.close()
