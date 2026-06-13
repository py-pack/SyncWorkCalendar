from datetime import datetime, UTC

from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.event import listens_for
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class APIUser(Base):
    __tablename__ = "api_users"

    username: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    # nullable — invite-флоу без пароля: адмін заводить користувача через
    # `POST /users`, той входить через Google за `email`. Логін/пароль для
    # такого рядка неможливий (роутер логіну дає 401 на NULL-хеш).
    password_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    # E-mail для зіставлення Google-акаунта (match-by-email). UNIQUE, але
    # nullable — старі рядки можуть бути без нього; зберігаємо у нижньому
    # регістрі (нормалізація — на рівні DAO/сервісу).
    email: Mapped[str | None] = mapped_column(
        String, nullable=True, unique=True
    )
    worker_key: Mapped[str | None] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


@listens_for(APIUser, "before_insert")
@listens_for(APIUser, "before_update")
def _stamp_api_user_timestamps(mapper, connection, target):
    now = datetime.now(UTC)
    if not target.created_at:
        target.created_at = now
    target.updated_at = now
