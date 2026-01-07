import bcrypt
from datetime import datetime, timedelta

MAX_FAILED_ATTEMPTS = 5
LOCK_TIME_MINUTES = 15


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode(), salt)
    return hashed.decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def is_account_locked(user: dict) -> bool:
    locked_until = user.get("locked_until")
    if locked_until is None:
        return False
    return datetime.utcnow() < locked_until


def register_failed_attempt(user: dict) -> dict:
    user["failed_attempts"] += 1

    if user["failed_attempts"] >= MAX_FAILED_ATTEMPTS:
        user["locked_until"] = datetime.utcnow() + timedelta(minutes=LOCK_TIME_MINUTES)
        user["failed_attempts"] = 0  # Reset nach Lock

    return user


def reset_failed_attempts(user: dict) -> dict:
    user["failed_attempts"] = 0
    user["locked_until"] = None
    return user