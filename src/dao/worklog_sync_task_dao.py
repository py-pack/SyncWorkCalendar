from datetime import datetime, time

from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from .base_dao import BaseDAO
from src.models import WorklogSyncTask, StatusTaskEnum


class WorklogSyncTaskDAO(BaseDAO):
    model = WorklogSyncTask

    @classmethod
    async def get_keys_period(cls, db: AsyncSession, start_date: datetime, end_date: datetime) -> set[str]:
        keys_query = await db.execute(
            select(WorklogSyncTask.issue_key).where(and_(
                WorklogSyncTask.status == StatusTaskEnum.pre_create,
                WorklogSyncTask.started_at >= datetime.combine(start_date.date(), time.min),
                WorklogSyncTask.started_at <= datetime.combine(end_date.date(), time.max),
            ))
        )
        return set(keys_query.scalars().all())
