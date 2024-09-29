import enum

from datetime import datetime, date
from .base import Base

from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import String, Integer, DateTime, Date, Enum


class StatusTaskEnum(enum.Enum):
    PRE_CREATE = "pre_create"
    CREATE = "create"
    CREATED = "created"
    PRE_UPDATE = "pre_update"
    UPDATE = "update"
    UPDATED = "updated"
    SYNC = "sync"


class WorklogSyncTask(Base):
    status: Mapped[StatusTaskEnum] = mapped_column(Enum(StatusTaskEnum), nullable=False)
    source_id: Mapped[int] = mapped_column(Integer, nullable=False)
    target_id: Mapped[int] = mapped_column(Integer, nullable=True)
    worker_key: Mapped[str] = mapped_column(String, nullable=False)
    issue_key: Mapped[str] = mapped_column(String, nullable=False)
    issue_id: Mapped[int] = mapped_column(Integer, nullable=True)
    content: Mapped[str] = mapped_column(String, nullable=True)
    started_at: Mapped[date] = mapped_column(Date(), nullable=False)
    time_spent: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
