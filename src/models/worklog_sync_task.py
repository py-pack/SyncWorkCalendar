import enum

from datetime import datetime, date, UTC

from .base import Base

from sqlalchemy import String, Integer, DateTime, Date, Enum
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy.event import listens_for


class StatusTaskEnum(enum.Enum):
    pre_create = "pre_create"
    create = "create"
    created = "created"
    pre_update = "pre_update"
    update = "update"
    updated = "updated"
    sync = "sync"


class WorklogSyncTask(Base):
    status: Mapped[StatusTaskEnum] = mapped_column(
        Enum(StatusTaskEnum, name="worklog_sync_status_task_enum"), nullable=False)
    source_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    target_id: Mapped[int] = mapped_column(Integer, nullable=True, index=True)
    worker_key: Mapped[str] = mapped_column(String, nullable=False)
    issue_key: Mapped[str] = mapped_column(String, nullable=False)
    issue_id: Mapped[int] = mapped_column(Integer, nullable=True, index=True)
    content: Mapped[str] = mapped_column(String, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    time_spent: Mapped[int] = mapped_column(Integer, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)


@listens_for(WorklogSyncTask, 'before_insert')
@listens_for(WorklogSyncTask, 'before_update')
def set_created_at(mapper, connection, target):
    date_now: datetime = datetime.now(UTC)
    if not target.created_at:
        target.created_at = date_now
    target.updated_at = date_now
