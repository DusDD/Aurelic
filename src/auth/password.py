import bcrypt

def hash_password(password: str) -> str:
    """Hash ein Passwort und gibt den Hash zurück"""
    pw_bytes = password.encode("utf-8")[:72]  # max 72 Bytes
    hashed = bcrypt.hashpw(pw_bytes, bcrypt.gensalt())
    return hashed.decode("utf-8")

def validate_password(password: str) -> tuple[bool, str]:
    """
    Prüft, ob Passwort gültig ist.
    Rückgabe: (True, "") wenn okay, sonst (False, "error_code")
    """
    if len(password) < 8:
        return False, "too_short"
    if not any(c.isdigit() for c in password):
        return False, "no_digit"
    if not any(c.isupper() for c in password):
        return False, "no_upper"
    return True, ""

def verify_password(password: str, hashed: str) -> bool:
    """
    Prüft ein Passwort gegen einen Hash.
    Rückgabe: True = korrekt, False = falsch
    """
    password_bytes = password.encode("utf-8")[:72]
    hashed_bytes = hashed.encode("utf-8")
    return bcrypt.checkpw(password_bytes, hashed_bytes)