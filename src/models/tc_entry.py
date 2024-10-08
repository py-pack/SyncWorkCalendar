from typing import TYPE_CHECKING

from sqlalchemy import Integer, String, JSON, DateTime, Computed
from sqlalchemy.event import listen
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.orm import relationship, foreign
from sqlalchemy.orm.attributes import flag_modified

from datetime import datetime

from .base import Base

if TYPE_CHECKING:
    from .tc_project import TCProject


class TCEntry(Base):
    __tablename__ = 'tc_entries'

    tc_project_id: Mapped[int] = mapped_column(Integer, nullable=True)
    description: Mapped[str] = mapped_column(String, nullable=True)
    meta: Mapped[dict] = mapped_column(JSON, nullable=True)
    start_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    duration: Mapped[int] = mapped_column(Integer, Computed("EXTRACT(EPOCH FROM end_at - start_at)"), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    tc_project = relationship(
        "TCProject",
        primaryjoin="foreign(TCEntry.tc_project_id) == TCProject.id",
        back_populates="ts_entries",
    )


def change_tc_entry_description(target: TCEntry, value: str | None, oldvalue: str | None, initiator):
    if value == oldvalue and target.meta is not None:
        return

    from src.core.utils import SyncTaskService
    task_key = SyncTaskService.match_task(value)
    if task_key:
        if target.meta is None:
            target.meta = dict()
        target.meta["task"] = task_key
        flag_modified(target, "meta")
    else:
        target.meta = None


listen(TCEntry.description, 'set', change_tc_entry_description)
