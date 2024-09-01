from datetime import datetime, time

from sqlalchemy import select, and_
from src.core import db_helper
from src.models import TCEntry

from .base_dao import BaseDAO


class TCEntriesDAO(BaseDAO):
    model = TCEntry

    @classmethod
    async def sync_all_between(cls, entries, date_from: datetime, date_to: datetime):
        async with db_helper.session_factory() as db:
            entries_db = (await db.execute(
                select(TCEntry).where(
                    and_(
                        TCEntry.start_at >= datetime.combine(date_from.date(), time.min),
                        TCEntry.start_at <= datetime.combine(date_to.date(), time.max),
                    )
                ))).scalars().all()

        await cls._sync(entries, entries_db)
