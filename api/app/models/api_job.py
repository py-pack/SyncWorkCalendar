import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import String, Text, DateTime, Enum, CheckConstraint, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class APIJobStatusEnum(enum.Enum):
    running = "running"
    needs_verification = "needs_verification"
    verified = "verified"
    failed = "failed"


class APIJob(Base):
    __tablename__ = "api_jobs"
    __table_args__ = (
        CheckConstraint(
            "verified_at IS NULL OR status = 'verified'",
            name="verified_at_only_when_verified",
        ),
        CheckConstraint(
            "finished_at IS NULL OR status <> 'running'",
            name="finished_at_only_when_not_running",
        ),
    )

    # Override Base.id (Integer) to use a UUID primary key.
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    trigger_name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    status: Mapped[APIJobStatusEnum] = mapped_column(
        Enum(APIJobStatusEnum, name="api_job_status_enum"),
        nullable=False,
        default=APIJobStatusEnum.running,
        index=True,
    )
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    result: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(String, nullable=False)
    verified_by: Mapped[str | None] = mapped_column(String, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
