from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class LoginRequest(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class GoogleAuthRequest(BaseModel):
    """Тіло `POST /auth/google` — рівно одне поле з двох.

    - `credential` — Google **ID-token** (One Tap / GIS credential-режим);
    - `code` — auth-**code** із popup-флоу (бекенд обмінює його в Google).
    """

    credential: str | None = None
    code: str | None = None

    @model_validator(mode="after")
    def _exactly_one(self) -> "GoogleAuthRequest":
        provided = [v for v in (self.credential, self.code) if v]
        if len(provided) != 1:
            raise ValueError("provide exactly one of: credential, code")
        return self


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class CurrentUserResponse(BaseModel):
    username: str
    worker_key: str | None
    expires_at: datetime
