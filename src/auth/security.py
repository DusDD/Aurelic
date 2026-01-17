import re
from datetime import datetime, timedelta
from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12
)

COMMON_PASSWORDS = {"password", "123456", "qwerty", "letmein", "abc123"}

# Account Lock (DB-basiert)
MAX_FAILED_ATTEMPTS = 5
LOCK_MINUTES = 15

# Rate Limiter (in-memory, kurzfristig)
FAILED_ATTEMPT_WINDOW = timedelta(minutes=1)
MAX_FAILED_PER_WINDOW = 5
user_failed_attempts = {}  # user_id: [timestamps]

def is_account_locked(user: dict) -> bool:
    locked_until = user.get("locked_until")
    if locked_until is None:
        return False
    return datetime.utcnow() < locked_until


def register_failed_login(user_id: int, conn):
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE auth.users
        SET failed_login_attempts = failed_login_attempts + 1
        WHERE id = %s
        RETURNING failed_login_attempts
    """, (user_id,))
    attempts = cursor.fetchone()[0]

    if attempts >= MAX_FAILED_ATTEMPTS:
        locked_until = datetime.utcnow() + timedelta(minutes=LOCK_MINUTES)
        cursor.execute("""
            UPDATE auth.users
            SET locked_until = %s
            WHERE id = %s
        """, (locked_until, user_id))

    conn.commit()


def check_rate_limit(key: str) -> bool:
    key = (key or "").strip().lower()
    if not key:
        return False

    now = datetime.utcnow()
    attempts = user_failed_attempts.get(key, [])

    # nur Versuche im Zeitfenster behalten
    attempts = [t for t in attempts if now - t < FAILED_ATTEMPT_WINDOW]

    if len(attempts) >= MAX_FAILED_PER_WINDOW:
        user_failed_attempts[key] = attempts  # optional: gespeichert lassen
        return False

    attempts.append(now)
    user_failed_attempts[key] = attempts
    return True