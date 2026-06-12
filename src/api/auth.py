"""JWT codec + bcrypt password hashing helpers.

The HTTP layer talks to this module instead of poking at ``bcrypt`` or
``jose`` directly; tests can swap implementations here.
"""
from datetime import datetime, timedelta, UTC
from typing import Any

import bcrypt
from jose import ExpiredSignatureError, JWTError, jwt

from src.config import settings


_JWT_ALGORITHM = "HS256"

# bcrypt operates on at most 72 bytes; longer secrets are truncated. We do it
# explicitly (and identically for hash + verify) so bcrypt 4.x/5.x does not
# raise on long passwords and verification stays consistent.
_BCRYPT_MAX_BYTES = 72


def _secret_bytes(plain: str) -> bytes:
    return plain.encode("utf-8")[:_BCRYPT_MAX_BYTES]


class TokenDecodeError(Exception):
    """Raised when a JWT cannot be decoded or has expired."""

    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(_secret_bytes(plain), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(_secret_bytes(plain), hashed.encode("utf-8"))
    except ValueError:
        # Malformed hash in the DB — treat as a verification failure rather
        # than crashing the request.
        return False


def create_access_token(
    *,
    sub: str,
    user_id: int,
    worker_key: str | None,
    ttl_hours: int | None = None,
) -> tuple[str, datetime]:
    now = datetime.now(UTC)
    hours = ttl_hours if ttl_hours is not None else settings.api.jwt_ttl_hours
    exp = now + timedelta(hours=hours)
    payload: dict[str, Any] = {
        "sub": sub,
        "user_id": user_id,
        "worker_key": worker_key,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    token = jwt.encode(payload, settings.api.jwt_secret, algorithm=_JWT_ALGORITHM)
    return token, exp


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.api.jwt_secret, algorithms=[_JWT_ALGORITHM])
    except ExpiredSignatureError as exc:
        raise TokenDecodeError("Token expired") from exc
    except JWTError as exc:
        raise TokenDecodeError("Invalid token") from exc
