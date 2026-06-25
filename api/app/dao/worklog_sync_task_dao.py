from datetime import datetime, time

from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from .base_dao import BaseDAO
from app.models import WorklogSyncTask, StatusTaskEnum


class WorklogSyncTaskDAO(BaseDAO):
    model = WorklogSyncTask

    @classmethod
    async def get_by_period_and_status(
        cls,
        db: AsyncSession,
        start_date: datetime,
        end_date: datetime,
        status: StatusTaskEnum | None,
    ) -> list[WorklogSyncTask]:
        conditions = [
            WorklogSyncTask.started_at
            >= datetime.combine(start_date.date(), time.min),
            WorklogSyncTask.started_at
            <= datetime.combine(end_date.date(), time.max),
        ]

        if status:
            conditions.append(WorklogSyncTask.status == status)

        keys_query = await db.execute(
            select(cls.model).where(and_(*conditions))
        )
        return list(keys_query.scalars().all())

    @classmethod
    async def get_by_source_ids(
        cls,
        db: AsyncSession,
        source_ids: list[int],
        worker_key: str,
    ) -> dict[int, WorklogSyncTask]:
        """Наявні WST за `source_id` (TimeCamp-запис) для одного `worker_key`.

        Ключ карти — `source_id`, тож реконсиляція робить upsert одним проходом
        (немає → створити; є → перелінк/оновлення). Scoped по `worker_key`, бо
        запис належить конкретному виконавцю.
        """
        if not source_ids:
            return {}
        rows = (
            (
                await db.execute(
                    select(cls.model).where(
                        and_(
                            cls.model.source_id.in_(source_ids),
                            cls.model.worker_key == worker_key,
                        )
                    )
                )
            )
            .scalars()
            .all()
        )
        return {row.source_id: row for row in rows}
