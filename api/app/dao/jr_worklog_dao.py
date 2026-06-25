from datetime import datetime, time
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import JRWorklog
from .base_dao import BaseDAO


class JRWorklogDAO(BaseDAO):
    model = JRWorklog

    @classmethod
    async def find_match(
        cls,
        db: AsyncSession,
        jr_issues_id: int,
        jr_worker_key: str,
        started_at: datetime,
        duration: int,
    ) -> JRWorklog | None:
        """Наявний Tempo-worklog для дедупу перед пушем (D5).

        Збіг за `(jr_issues_id, jr_worker_key, started_at, duration)`. Для v1 —
        **точний** збіг часу початку (до секунди) і тривалості; толерантність до
        округлення/таймзон — відкрите питання QA (`design.md` → Open Questions).
        `JRWorklog.id` == Tempo `originId`, тож знайдений рядок одразу дає
        `target_id` для `WorklogSyncTask`.
        """
        stmt = select(cls.model).where(
            and_(
                cls.model.jr_issues_id == jr_issues_id,
                cls.model.jr_worker_key == jr_worker_key,
                cls.model.started_at == started_at,
                cls.model.duration == duration,
            )
        )
        return (await db.execute(stmt)).scalars().first()

    @classmethod
    async def sync_all_between(
        cls, db: AsyncSession, worklogs, date_from: datetime, date_to: datetime
    ):
        worklogs_db = (
            (
                await db.execute(
                    select(cls.model).where(
                        and_(
                            cls.model.started_at
                            >= datetime.combine(date_from.date(), time.min),
                            cls.model.started_at
                            <= datetime.combine(date_to.date(), time.max),
                        )
                    )
                )
            )
            .scalars()
            .all()
        )

        await cls._sync(db, worklogs, worklogs_db)
