"""JWT codec + bcrypt password hashing helpers.

The HTTP layer talks to this module instead of poking at ``bcrypt`` or
``jose`` directly; tests can swap implementations here.
"""

from datetime import datetime, timedelta, UTC
from typing import Any

import bcrypt
import requests
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from jose import ExpiredSignatureError, JWTError, jwt

from app.config import settings


_JWT_ALGORITHM = "HS256"

# Google OAuth: дозволені issuer-и для ID-token і endpoint обміну auth-code.
_GOOGLE_ISSUERS = {"accounts.google.com", "https://accounts.google.com"}
_GOOGLE_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
# redirect_uri для GIS popup code-флоу (`initCodeClient`, `ux_mode: 'popup'`).
_GOOGLE_POPUP_REDIRECT = "postmessage"

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


class GoogleVerifyError(Exception):
    """Raised when a Google credential/code cannot be verified."""

    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


def verify_google_credential(credential: str, *, client_id: str) -> str:
    """Серверно верифікувати Google ID-token і повернути e-mail.

    Через бібліотеку ``google-auth`` перевіряється підпис (Google JWKS),
    ``aud == client_id``, issuer і ``exp``; додатково вимагається
    ``email_verified``. Будь-яка невдача → ``GoogleVerifyError`` (мапиться у
    401 на рівні роутера). Клієнтським даним не довіряємо без перевірки.
    """
    try:
        claims = google_id_token.verify_oauth2_token(
            credential, google_requests.Request(), client_id
        )
    except ValueError as exc:
        # Невалідний підпис / прострочений / невірний aud — усе сюди.
        raise GoogleVerifyError("invalid google credential") from exc

    if claims.get("iss") not in _GOOGLE_ISSUERS:
        raise GoogleVerifyError("invalid issuer")
    if not claims.get("email_verified"):
        raise GoogleVerifyError("email not verified")
    email = claims.get("email")
    if not email:
        raise GoogleVerifyError("no email in credential")
    return email


def exchange_google_code(
    code: str, *, client_id: str, client_secret: str
) -> str:
    """Обміняти popup auth-`code` у Google на токени і повернути ID-token.

    ``redirect_uri='postmessage'`` — конвенція GIS popup-флоу. Невдалий обмін
    (битий/використаний код) → ``GoogleVerifyError`` (→ 401); мережеві збої
    ``requests`` бульбашаться у глобальний 502-handler.
    """
    resp = requests.post(
        _GOOGLE_TOKEN_ENDPOINT,
        data={
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": _GOOGLE_POPUP_REDIRECT,
            "grant_type": "authorization_code",
        },
        timeout=10,
    )
    if resp.status_code != 200:
        raise GoogleVerifyError("code exchange failed")
    id_tok = resp.json().get("id_token")
    if not id_tok:
        raise GoogleVerifyError("no id_token in exchange response")
    return id_tok


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(_secret_bytes(plain), bcrypt.gensalt()).decode(
        "utf-8"
    )


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
    token = jwt.encode(
        payload, settings.api.jwt_secret, algorithm=_JWT_ALGORITHM
    )
    return token, exp


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(
            token, settings.api.jwt_secret, algorithms=[_JWT_ALGORITHM]
        )
    except ExpiredSignatureError as exc:
        raise TokenDecodeError("Token expired") from exc
    except JWTError as exc:
        raise TokenDecodeError("Invalid token") from exc
