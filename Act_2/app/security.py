from datetime import datetime, timedelta, timezone
from uuid import uuid4
import jwt
from argon2 import PasswordHasher
from argon2.low_level import Type
from app.config import settings


# Hash de contraseñas (Argon2id)
ph = PasswordHasher(
time_cost=3,
memory_cost=64 * 1024, # 64 MB
parallelism=2,
hash_len=32,
salt_len=16,
type=Type.ID,
)


def hash_password(password: str) -> str:
    return ph.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return ph.verify(password_hash, password)
    except Exception:
        return False


# JWT utilidades
ALGO = "HS256"


class TokenPair:
    def __init__(self, access: str, refresh: str):
        self.access = access
        self.refresh = refresh




    def _encode(payload: dict, key: str, minutes: int | None = None, days: int | None = None) -> str:
        now = datetime.now(timezone.utc)
        exp = now + (timedelta(minutes=minutes) if minutes else timedelta(days=days or 0))
        payload = {**payload, "iat": int(now.timestamp()), "exp": int(exp.timestamp())}
        return jwt.encode(payload, key, algorithm=ALGO)




def create_access_token(user_id: str) -> str:
    jti = uuid4().hex
    return _encode({"sub": user_id, "jti": jti, "typ": "access"}, settings.SECRET_KEY, minutes=settings.ACCESS_TOKEN_EXPIRES_MIN)




def create_refresh_token(user_id: str, jti: str | None = None) -> str:
    return _encode({"sub": user_id, "jti": jti or uuid4().hex, "typ": "refresh"}, settings.REFRESH_SECRET_KEY, days=settings.REFRESH_TOKEN_EXPIRES_DAYS)




def decode_access(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGO])




def decode_refresh(token: str) -> dict:
    return jwt.decode(token, settings.REFRESH_SECRET_KEY, algorithms=[ALGO])
