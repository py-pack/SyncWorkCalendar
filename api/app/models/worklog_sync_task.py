import enum

from datetime import datetime, date, UTC

from .base import Base

from sqlalchemy import String, Integer, DateTime, Date, Enum, ForeignKey
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
    # Місток до TimeCamp-запису (`tc_entries.id`): лише `UNIQUE` (один WST на запис),
    # БЕЗ FK — історію WST не чіпаємо каскадом при зникненні запису (різні сервіси,
    # синхронимо за можливості; D3 у `harden-worklog-link`).
    source_id: Mapped[int] = mapped_column(
        Integer, nullable=False, unique=True, index=True
    )
    # Місток до Tempo-worklog-а (`jr_worklogs.id`): FK із `ON DELETE SET NULL` —
    # коли worklog зникає з Tempo, лінк занулюється без дангл-посилань (D2).
    target_id: Mapped[int] = mapped_column(
        ForeignKey("jr_worklogs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
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
