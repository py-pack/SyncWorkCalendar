from datetime import datetime, time
from sqlalchemy import select, and_
from src.models import JRWorklog
from src.core import db_helper
from .base_dao import BaseDAO


class JRWorklogDAO(BaseDAO):
    model = JRWorklog

    @classmethod
    async def sync_all_between(cls, worklogs, date_from: datetime, date_to: datetime):
        async with db_helper.session_factory() as db:
            worklogs_db = (await db.execute(
                select(cls.model).where(
                    and_(
                        cls.model.started_at >= datetime.combine(date_from.date(), time.min),
                        cls.model.started_at <= datetime.combine(date_to.date(), time.max),
                    )
                ))).scalars().all()

        await cls._sync(worklogs, worklogs_db)
