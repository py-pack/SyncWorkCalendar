from datetime import datetime, time

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import TCEntry

from .base_dao import BaseDAO


class TCEntriesDAO(BaseDAO):
    model = TCEntry

    @classmethod
    async def sync_all_between(cls, db: AsyncSession, entries, date_from: datetime, date_to: datetime):
        entries_db = (await db.execute(
            select(cls.model).where(
                and_(
                    cls.model.start_at >= datetime.combine(date_from.date(), time.min),
                    cls.model.start_at <= datetime.combine(date_to.date(), time.max),
                )
            ))).scalars().all()

        await cls._sync(db, entries, entries_db)
