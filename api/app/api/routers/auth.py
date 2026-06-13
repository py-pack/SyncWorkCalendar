from datetime import datetime, UTC

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import (
    GoogleVerifyError,
    create_access_token,
    exchange_google_code,
    verify_google_credential,
    verify_password,
)
from app.api.deps import CurrentUser, get_current_user, get_db, get_settings
from app.api.schemas.auth import (
    CurrentUserResponse,
    GoogleAuthRequest,
    LoginRequest,
    TokenResponse,
)
from app.config import Settings
from app.dao import APIUserDAO


router = APIRouter()


_INVALID_CREDENTIALS = "Invalid credentials"
# Невідомий/неактивний e-mail і будь-яка невдача верифікації → однакова 401,
# щоб не розрізняти «акаунт існує / ні».
_ACCOUNT_NOT_FOUND = "account not found"


def _seconds_until(ts: datetime) -> int:
    return max(0, int((ts - datetime.now(UTC)).total_seconds()))


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> TokenResponse:
    user = await APIUserDAO.get_by_username(db, body.username)
    # Unified 401 for unknown user / wrong password / inactive / passwordless —
    # by spec ``api-auth.Scenario: Wrong password``, ``Unknown username``,
    # ``Inactive user`` + invite-флоу (``password_hash IS NULL`` → вхід лише
    # через Google; перевіряємо до verify_password, бо той не приймає None).
    if (
        user is None
        or not user.is_active
        or user.password_hash is None
        or not verify_password(body.password, user.password_hash)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_INVALID_CREDENTIALS,
        )

    token, exp = create_access_token(
        sub=user.username,
        user_id=user.id,
        worker_key=user.worker_key,
    )
    return TokenResponse(access_token=token, expires_in=_seconds_until(exp))


@router.post("/google", response_model=TokenResponse)
async def google_auth(
    body: GoogleAuthRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> TokenResponse:
    # Публічний маршрут (як /auth/login) — без get_current_user.
    client_id = settings.api.google_client_id
    if not client_id:
        # Google-вхід не налаштований → 503 (не 500); логін/пароль не зачеплено.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="google sign-in is not configured",
        )

    # Отримати ID-token: або напряму (credential), або через обмін code.
    if body.code is not None:
        if not settings.api.google_client_secret:
            # code-гілка потребує secret — без нього 503 (не 500).
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="google code flow is not configured",
            )
        try:
            credential = exchange_google_code(
                body.code,
                client_id=client_id,
                client_secret=settings.api.google_client_secret,
            )
        except GoogleVerifyError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=_ACCOUNT_NOT_FOUND,
            )
    else:
        credential = body.credential

    try:
        email = verify_google_credential(credential, client_id=client_id)
    except GoogleVerifyError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=_ACCOUNT_NOT_FOUND
        )

    # match-by-email (lower-case, лише активні); без авто-реєстрації.
    user = await APIUserDAO.get_by_email(db, email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=_ACCOUNT_NOT_FOUND
        )

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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    token, exp = create_access_token(
        sub=user.username,
        user_id=user.id,
        worker_key=user.worker_key,
    )
    return TokenResponse(access_token=token, expires_in=_seconds_until(exp))


@router.get("/me", response_model=CurrentUserResponse)
async def me(
    current: CurrentUser = Depends(get_current_user),
) -> CurrentUserResponse:
    return CurrentUserResponse(
        username=current.username,
        worker_key=current.worker_key,
        expires_at=datetime.fromtimestamp(current.exp_ts, tz=UTC),
    )
