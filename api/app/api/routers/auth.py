from datetime import datetime, UTC

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import create_access_token, verify_password
from app.api.deps import CurrentUser, get_current_user, get_db, get_settings
from app.api.schemas.auth import CurrentUserResponse, LoginRequest, TokenResponse
from app.config import Settings
from app.dao import APIUserDAO


router = APIRouter()


_INVALID_CREDENTIALS = "Invalid credentials"


def _seconds_until(ts: datetime) -> int:
    return max(0, int((ts - datetime.now(UTC)).total_seconds()))


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> TokenResponse:
    user = await APIUserDAO.get_by_username(db, body.username)
    # Unified 401 for unknown user / wrong password / inactive — by spec
    # ``api-auth.Scenario: Wrong password``, ``Unknown username``, ``Inactive user``.
    if user is None or not user.is_active or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=_INVALID_CREDENTIALS)

    token, exp = create_access_token(
        sub=user.username,
        user_id=user.id,
        worker_key=user.worker_key,
    )
    return TokenResponse(access_token=token, expires_in=_seconds_until(exp))


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    # ``get_current_user`` already verified the token (incl. exp) and that the
    # user is still active. Reissue with a fresh exp.
    user = await APIUserDAO.find(db, current.id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    token, exp = create_access_token(
        sub=user.username,
        user_id=user.id,
        worker_key=user.worker_key,
    )
    return TokenResponse(access_token=token, expires_in=_seconds_until(exp))


@router.get("/me", response_model=CurrentUserResponse)
async def me(current: CurrentUser = Depends(get_current_user)) -> CurrentUserResponse:
    return CurrentUserResponse(
        username=current.username,
        worker_key=current.worker_key,
        expires_at=datetime.fromtimestamp(current.exp_ts, tz=UTC),
    )
