import uuid
from datetime import datetime, time, UTC
from typing import Any

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import APIJob, APIJobStatusEnum

from .base_dao import BaseDAO


class APIJobDAO(BaseDAO):
    model = APIJob

    @classmethod
    async def create_running(
        cls,
        db: AsyncSession,
        trigger_name: str,
        payload: dict[str, Any] | None,
        created_by: str,
    ) -> APIJob:
        job = APIJob(
            trigger_name=trigger_name,
            status=APIJobStatusEnum.running,
            payload=payload,
            created_by=created_by,
            started_at=datetime.now(UTC),
        )
        db.add(job)
        await db.flush()
        await db.refresh(job)
        return job

    @classmethod
    async def mark_needs_verification(
        cls,
        db: AsyncSession,
        job_id: uuid.UUID,
        result: dict[str, Any] | None,
    ) -> APIJob | None:
        job = await db.get(cls.model, job_id)
        if job is None:
            return None
        job.status = APIJobStatusEnum.needs_verification
        job.result = result
        job.finished_at = datetime.now(UTC)
        await db.flush()
        return job

    @classmethod
    async def mark_failed(
        cls,
        db: AsyncSession,
        job_id: uuid.UUID,
        error: str,
    ) -> APIJob | None:
        job = await db.get(cls.model, job_id)
        if job is None:
            return None
        job.status = APIJobStatusEnum.failed
        job.error = error
        job.finished_at = datetime.now(UTC)
        await db.flush()
        return job

    @classmethod
    async def mark_verified(
        cls,
        db: AsyncSession,
        job_id: uuid.UUID,
        verified_by: str,
    ) -> tuple[APIJob | None, str | None]:
        """Atomically transition needs_verification -> verified.

        Returns ``(job, error)``. ``error`` is one of:
        - ``"not_found"`` when no row exists.
        - ``"already_terminal"`` when status is ``verified`` or ``failed``.
        - ``"not_finished"`` when status is still ``running``.
        - ``None`` on success.
        """
        job = await db.get(cls.model, job_id)
        if job is None:
            return None, "not_found"
        if job.status in (APIJobStatusEnum.verified, APIJobStatusEnum.failed):
            return job, "already_terminal"
        if job.status == APIJobStatusEnum.running:
            return job, "not_finished"
        job.status = APIJobStatusEnum.verified
        job.verified_by = verified_by
        job.verified_at = datetime.now(UTC)
        await db.flush()
        return job, None

    @classmethod
    async def get_by_id(cls, db: AsyncSession, job_id: uuid.UUID) -> APIJob | None:
        return await db.get(cls.model, job_id)

    @classmethod
    async def list_filtered(
        cls,
        db: AsyncSession,
        status: APIJobStatusEnum | None = None,
        trigger_name: str | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[APIJob], int]:
        conditions = []
        if status is not None:
            conditions.append(cls.model.status == status)
        if trigger_name is not None:
            conditions.append(cls.model.trigger_name == trigger_name)
        if start is not None:
            conditions.append(cls.model.started_at >= datetime.combine(start.date(), time.min))
        if end is not None:
            conditions.append(cls.model.started_at <= datetime.combine(end.date(), time.max))

        base_where = and_(*conditions) if conditions else None

        items_query = select(cls.model)
        count_query = select(func.count()).select_from(cls.model)
        if base_where is not None:
            items_query = items_query.where(base_where)
            count_query = count_query.where(base_where)

        items_query = items_query.order_by(cls.model.started_at.desc()).limit(limit).offset(offset)

        items_result = await db.execute(items_query)
        items = list(items_result.scalars().all())

        count_result = await db.execute(count_query)
        total = int(count_result.scalar_one())

        return items, total
