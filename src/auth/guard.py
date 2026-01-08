from .token import verify_token


def require_auth(token: str) -> int:
    user_id = verify_token(token)
    if user_id is None:
        raise PermissionError("Unauthorized")
    return user_id