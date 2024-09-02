from datetime import datetime

from sqlalchemy import Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class JRIssue(Base):
    key: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String, nullable=False)

    jr_project_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    epic_key: Mapped[str] = mapped_column(String, nullable=True, index=True)
    parent_key: Mapped[str] = mapped_column(String, nullable=True, index=True)

    type: Mapped[str] = mapped_column(String, nullable=False)
    priority: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)

    jr_creator_id: Mapped[int] = mapped_column(Integer, nullable=True, index=True)
    jr_reporter_id: Mapped[int] = mapped_column(Integer, nullable=True, index=True)

    # timeoriginalestimate
    estimate_plan: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # aggregateprogress->progress
    estimate_fact: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # aggregatetimeestimate
    estimate_rest: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
