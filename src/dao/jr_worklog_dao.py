from datetime import datetime, time
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from src.models import JRWorklog
from .base_dao import BaseDAO


class JRWorklogDAO(BaseDAO):
    model = JRWorklog

    @classmethod
    async def sync_all_between(cls, db: AsyncSession, worklogs, date_from: datetime, date_to: datetime):
        worklogs_db = (await db.execute(
            select(cls.model).where(
                and_(
                    cls.model.started_at >= datetime.combine(date_from.date(), time.min),
                    cls.model.started_at <= datetime.combine(date_to.date(), time.max),
                )
            ))).scalars().all()

        await cls._sync(db, worklogs, worklogs_db)
