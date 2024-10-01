from typing import List, TYPE_CHECKING

from sqlalchemy import DateTime, String, Integer, SmallInteger, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.orm import relationship, foreign
from datetime import datetime

from .base import Base

# Умовний імпорт для типізації
if TYPE_CHECKING:
    from .tc_entry import TCEntry


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

    ts_entries: Mapped[List["TCEntry"]] = relationship(
        "TCEntry",
        # uselist=True,
        primaryjoin="TCProject.id == foreign(TCEntry.tc_project_id)",  # Явний опис зв'язку
        back_populates="tc_project",
    )
