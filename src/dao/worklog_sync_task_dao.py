from datetime import datetime, time

from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from .base_dao import BaseDAO
from src.models import WorklogSyncTask, StatusTaskEnum


class WorklogSyncTaskDAO(BaseDAO):
    model = WorklogSyncTask

    @classmethod
    async def get_by_period_and_status(
        cls,
        db: AsyncSession,
        start_date: datetime,
        end_date: datetime,
        status: StatusTaskEnum | None
    ) -> list[WorklogSyncTask]:
        conditions = [
            WorklogSyncTask.started_at >= datetime.combine(start_date.date(), time.min),
            WorklogSyncTask.started_at <= datetime.combine(end_date.date(), time.max),
        ]

        if status:
            conditions.append(WorklogSyncTask.status == status)

        keys_query = await db.execute(
            select(cls.model).where(and_(*conditions))
        )
        return list(keys_query.scalars().all())
