from datetime import datetime, timedelta, timezone
from typing import Any, Optional
import bcrypt
from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,
    bcrypt__truncate_error=False,
)


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def _encode(payload: dict) -> str:
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


def create_access_token(subject: Any, role: str = "") -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return _encode({"sub": str(subject), "role": role, "exp": exp, "type": "access"})


def create_refresh_token(subject: Any, role: str = "") -> str:
    exp = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return _encode({"sub": str(subject), "role": role, "exp": exp, "type": "refresh"})


def create_reset_token(email: str) -> str:
    exp = datetime.now(timezone.utc) + timedelta(hours=1)
    return _encode({"sub": email, "exp": exp, "type": "pwd_reset"})


def verify_reset_token(token: str) -> Optional[str]:
    try:
        payload = decode_token(token)
        if payload.get("type") != "pwd_reset":
            return None
        return payload.get("sub")
    except Exception:
        return None