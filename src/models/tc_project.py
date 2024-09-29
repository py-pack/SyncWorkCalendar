from sqlalchemy import DateTime, String, Integer, SmallInteger, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

from .base import Base


class TCProject(Base):
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    parent_id: Mapped[int] = mapped_column(Integer, nullable=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=True)

    level: Mapped[int] = mapped_column(SmallInteger, default=1)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    is_sync: Mapped[bool] = mapped_column(Boolean, default=False)

    issue_key: Mapped[str] = mapped_column(String, nullable=True)
    color: Mapped[str] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
