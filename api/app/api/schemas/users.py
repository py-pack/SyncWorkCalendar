from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserItem(BaseModel):
    """Користувач у відповіді `GET/POST/PATCH /users` — без `password_hash`."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    # `username` слугує і логіном, і відображуваним ім'ям (рішення: окрему
    # колонку `name` не додаємо).
    username: str
    email: EmailStr | None
    worker_key: str | None
    is_active: bool


class UserCreate(BaseModel):
    """Тіло `POST /users` — invite без пароля (вхід через Google за `email`).

    `password` опційний: якщо переданий — користувач зможе входити й
    логіном/паролем; якщо ні — `password_hash = NULL` і вхід лише через Google.
    """

    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=1)
    email: EmailStr
    worker_key: str | None = None
    password: str | None = Field(default=None, min_length=1)


class UserPatch(BaseModel):
    """Тіло `PATCH /users/{id}` — `email` не змінюється (це Google-ідентичність)."""

    model_config = ConfigDict(extra="forbid")

    username: str | None = Field(default=None, min_length=1)
    worker_key: str | None = None
    is_active: bool | None = None
