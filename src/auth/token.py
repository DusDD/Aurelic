import jwt
from datetime import datetime, timedelta

SECRET_KEY = "super-secret-key"
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 30

# In-Memory Blacklist (für lokal ok)
blacklisted_tokens = set()


def create_token(user_id: int):
    payload = {
        "sub": str(user_id),
        "exp": datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str):
    # in-memory blacklist
    if token in blacklisted_tokens:
        raise Exception("Token revoked")

    # DB blacklist (authoritative)
    try:
        from data.db_connection import get_connection
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM auth.revoked_tokens WHERE token = %s", (token,))
        revoked = cur.fetchone() is not None
        cur.close()
        conn.close()
        if revoked:
            raise Exception("Token revoked")
    except Exception as e:
        # If DB check fails, better to fail closed in production.
        # For development you might want fail-open, but security-wise fail-closed:
        raise Exception(f"Token verification failed: {e}")

    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


def blacklist_token(token: str):
    blacklisted_tokens.add(token)
