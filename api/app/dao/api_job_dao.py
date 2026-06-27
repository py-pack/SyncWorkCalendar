import uuid
from datetime import datetime, time, UTC
from typing import Any

from sqlalchemy import select, func, and_, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import APIJob, APIJobStatusEnum

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
    async def retry_claim(cls, db: AsyncSession, job_id: uuid.UUID) -> bool:
        """Атомарний compare-and-swap `failed → running` для ретраю (єдиний guard).

        Один `UPDATE ... WHERE id=:id AND status='failed'` переводить рядок у
        `running` і скидає поля наслідку (`finished_at`/`error`/`result` → NULL,
        `started_at` → now), не порушуючи CHECK `finished_at_only_when_not_running`.
        Повертає `True`, якщо рядок захоплено (`rowcount == 1`), інакше `False`
        (job-а не `failed`: уже `running` від попереднього кліку, інший статус або
        її нема). Row-level lock БД робить паралельний клік безпечним — зачепити
        рядок зможе лише один `UPDATE`, тож одночасно стартує лише один ретрай.
        """
        stmt = (
            update(cls.model)
            .where(
                cls.model.id == job_id,
                cls.model.status == APIJobStatusEnum.failed,
            )
            .values(
                status=APIJobStatusEnum.running,
                started_at=datetime.now(UTC),
                finished_at=None,
                error=None,
                result=None,
            )
        )
        result = await db.execute(stmt)
        return int(result.rowcount or 0) == 1

    @classmethod
    async def get_by_id(cls, db: AsyncSession, job_id: uuid.UUID) -> APIJob | None:
        return await db.get(cls.model, job_id)

    @classmethod
    async def verify_matching(
        cls,
        db: AsyncSession,
        *,
        trigger_name: str | None,
        start: datetime | None,
        end: datetime | None,
        verified_by: str,
    ) -> int:
        """Масово перевести `needs_verification`→`verified` за фільтрами.

        Один атомарний `UPDATE` (без поштучного циклу): дзеркалить набір фільтрів
        `list_filtered` (`trigger_name` + період за `started_at`), але `status`
        жорстко `needs_verification` — термінальні/`running` не зачіпаються (state
        machine). Ставить `verified_at=now()` разом зі `status=verified` (DB CHECK
        `verified_at_only_when_verified`). Повертає кількість підтверджених.
        """
        conditions = [cls.model.status == APIJobStatusEnum.needs_verification]
        if trigger_name is not None:
            conditions.append(cls.model.trigger_name == trigger_name)
        if start is not None:
            conditions.append(cls.model.started_at >= datetime.combine(start.date(), time.min))
        if end is not None:
            conditions.append(cls.model.started_at <= datetime.combine(end.date(), time.max))

        stmt = (
            update(cls.model)
            .where(and_(*conditions))
            .values(
                status=APIJobStatusEnum.verified,
                verified_by=verified_by,
                verified_at=datetime.now(UTC),
            )
        )
        result = await db.execute(stmt)
        return int(result.rowcount or 0)

    @classmethod
    async def auto_verify_older_than(cls, db: AsyncSession, older_than: datetime) -> int:
        """Авто-verify старих `needs_verification` (`finished_at < older_than`).

        `verified_by="system"` (системний, не людина). Лише `needs_verification`
        (state machine), повертає кількість зачеплених рядків.
        """
        stmt = (
            update(cls.model)
            .where(
                cls.model.status == APIJobStatusEnum.needs_verification,
                cls.model.finished_at < older_than,
            )
            .values(
                status=APIJobStatusEnum.verified,
                verified_by="system",
                verified_at=datetime.now(UTC),
            )
        )
        result = await db.execute(stmt)
        return int(result.rowcount or 0)

    @classmethod
    async def delete_terminal_older_than(cls, db: AsyncSession, older_than: datetime) -> int:
        """TTL-видалення термінальних (`verified`/`failed`) із `finished_at < older_than`.

        `running` і `needs_verification` **ніколи** не видаляються. Повертає
        кількість видалених рядків.
        """
        stmt = delete(cls.model).where(
            cls.model.status.in_((APIJobStatusEnum.verified, APIJobStatusEnum.failed)),
            cls.model.finished_at < older_than,
        )
        result = await db.execute(stmt)
        return int(result.rowcount or 0)

    @classmethod
    async def status_summary(
        cls,
        db: AsyncSession,
        *,
        trigger_name: str | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> dict[str, int]:
        """`COUNT(*) GROUP BY status` за періодом+тригером (ігнорує фільтр статусу).

        Усі 4 ключі присутні (нулі для відсутніх) — повна картина вибірки для
        зведення в тулбарі. Прецедент — `summary` у `GET /worklog-sync-tasks`.
        """
        conditions = []
        if trigger_name is not None:
            conditions.append(cls.model.trigger_name == trigger_name)
        if start is not None:
            conditions.append(cls.model.started_at >= datetime.combine(start.date(), time.min))
        if end is not None:
            conditions.append(cls.model.started_at <= datetime.combine(end.date(), time.max))

        stmt = select(cls.model.status, func.count()).group_by(cls.model.status)
        if conditions:
            stmt = stmt.where(and_(*conditions))

        rows = (await db.execute(stmt)).all()
        summary = {member.value: 0 for member in APIJobStatusEnum}
        for status_enum, cnt in rows:
            summary[status_enum.value] = int(cnt)
        return summary

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
