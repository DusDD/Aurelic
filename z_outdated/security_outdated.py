# def hash_password(password: str) -> str:
#    return pwd_context.hash(password)


# def verify_password(password: str, hashed: str) -> bool:
#    return pwd_context.verify(password, hashed)


# def validate_password(password: str) -> tuple[bool, str]:
#    if len(password) < 8:
#        return False, "too_short"
#    if not re.search(r"[A-Z]", password):
#        return False, "missing_upper"
#    if not re.search(r"[a-z]", password):
#        return False, "missing_lower"
#    if not re.search(r"[0-9]", password):
#        return False, "missing_number"
#    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
#        return False, "missing_special"
#    if password.lower() in COMMON_PASSWORDS:
#        return False, "too_common"
#    return True, ""