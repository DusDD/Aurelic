import jwt
from datetime import datetime, timedelta

SECRET_KEY = "dev-secret-change-later"
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 30


def create_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)



def verify_token(token: str) -> int | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return int(payload.get("sub"))  # ← zurück in int
    except Exception:
        return None