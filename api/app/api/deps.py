from dataclasses import dataclass
from typing import AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, settings
from app.core.db_helper import async_session_maker
from app.dao import APIUserDAO

from .auth import TokenDecodeError, decode_access_token


@dataclass
class CurrentUser:
    """Lightweight view of an authenticated user pulled from JWT + DB."""

    id: int
    username: str
    worker_key: str | None
    exp_ts: int  # JWT "exp" claim, seconds since epoch


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields one ``AsyncSession`` per request.

    Mirrors the contract of ``app.core.db_helper.get_async_asession``: commit
    on a clean exit, rollback on exception.
    """
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        else:
            await session.commit()


def get_settings() -> Settings:
    return settings


# Use auto_error=False so we can return a uniform 401 with our own message
# instead of FastAPI's "Not authenticated" 403 default.
_bearer_scheme = HTTPBearer(auto_error=False)


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> CurrentUser:
    if credentials is None or not credentials.credentials:
        raise _unauthorized("Not authenticated")

    try:
        claims = decode_access_token(credentials.credentials)
    except TokenDecodeError as exc:
        raise _unauthorized(exc.reason) from exc

    user_id = claims.get("user_id")
    username = claims.get("sub")
    if user_id is None or username is None:
        raise _unauthorized("Invalid token")

    # Re-read the row so deactivated users cannot keep using outstanding tokens.
    db_user = await APIUserDAO.find(db, user_id)
    if db_user is None or not db_user.is_active or db_user.username != username:
        raise _unauthorized("Invalid token")

    return CurrentUser(
        id=db_user.id,
        username=db_user.username,
        worker_key=db_user.worker_key,
        exp_ts=int(claims.get("exp", 0)),
    )
