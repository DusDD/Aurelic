from src.auth.session_state import SESSION

class NotAuthenticatedError(RuntimeError):
    pass


def require_session_token() -> str:
    token = SESSION.token
    if not token:
        raise NotAuthenticatedError("User not authenticated")
    return token
