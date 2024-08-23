from sqlalchemy import DateTime, String, Integer, SmallInteger, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

from .base import Base


class TCProject(Base):
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    parent_id: Mapped[int] = mapped_column(Integer, nullable=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=True)

    level: Mapped[int] = mapped_column(SmallInteger, default=0)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    is_synced: Mapped[bool] = mapped_column(Boolean, default=False)
    color: Mapped[str] = mapped_column(String, nullable=True)
    add_date_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    modify_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
