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
    if token in blacklisted_tokens:
        raise Exception("Token revoked")

    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


def blacklist_token(token: str):
    blacklisted_tokens.add(token)
