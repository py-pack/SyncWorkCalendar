from datetime import datetime, UTC

from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.event import listens_for
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class APIUser(Base):
    __tablename__ = "api_users"

    username: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    worker_key: Mapped[str | None] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


@listens_for(APIUser, "before_insert")
@listens_for(APIUser, "before_update")
def _stamp_api_user_timestamps(mapper, connection, target):
    now = datetime.now(UTC)
    if not target.created_at:
        target.created_at = now
    target.updated_at = now
