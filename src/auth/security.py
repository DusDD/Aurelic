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


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


def validate_password(password: str) -> tuple[bool, str]:
    if len(password) < 8:
        return False, "too_short"
    if not re.search(r"[A-Z]", password):
        return False, "missing_upper"
    if not re.search(r"[a-z]", password):
        return False, "missing_lower"
    if not re.search(r"[0-9]", password):
        return False, "missing_number"
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "missing_special"
    if password.lower() in COMMON_PASSWORDS:
        return False, "too_common"
    return True, ""


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


def check_rate_limit(user_id: int) -> bool:
    now = datetime.utcnow()
    attempts = user_failed_attempts.get(user_id, [])

    attempts = [t for t in attempts if now - t < FAILED_ATTEMPT_WINDOW]

    if len(attempts) >= MAX_FAILED_PER_WINDOW:
        return False

    attempts.append(now)
    user_failed_attempts[user_id] = attempts
    return True