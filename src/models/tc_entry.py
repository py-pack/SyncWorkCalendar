from sqlalchemy import Integer, String, JSON, DateTime, Computed
from sqlalchemy.orm import Mapped, mapped_column

from datetime import datetime

from .base import Base


class TCEntry(Base):
    __tablename__ = 'tc_entries'

    tc_project_id: Mapped[int] = mapped_column(Integer, nullable=True)
    description: Mapped[str] = mapped_column(String, nullable=True)
    meta: Mapped[dict] = mapped_column(JSON, nullable=True)
    start_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    duration: Mapped[int] = mapped_column(Integer, Computed("EXTRACT(EPOCH FROM end_at - start_at)"), nullable=False)
    modify_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
