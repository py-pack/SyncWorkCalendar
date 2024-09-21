from datetime import datetime
from sqlalchemy import Integer, String, JSON, DateTime, Date
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base


class JRWorklog(Base):
    jr_issues_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    meta: Mapped[dict] = mapped_column(JSON, nullable=True)

    jr_worker_key: Mapped[str] = mapped_column(String, nullable=True, index=True)
    started_at: Mapped[datetime] = mapped_column(Date(), nullable=False)
    duration: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
