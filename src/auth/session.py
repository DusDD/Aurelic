from .token import verify_token

def require_auth(token: str):
    try:
        payload = verify_token(token)
        return payload["sub"]
    except Exception as e:
        print("TOKEN DEBUG:", e)
        raise PermissionError("Unauthorized")