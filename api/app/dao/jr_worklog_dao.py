from datetime import date, datetime, time
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import JRIssue, JRWorklog, WorklogSyncTask
from .base_dao import BaseDAO


class JRWorklogDAO(BaseDAO):
    model = JRWorklog

    @classmethod
    async def list_with_link_state(
        cls,
        db: AsyncSession,
        worker_key: str | None,
        date_from: date,
        date_to: date,
        linked: str = "all",
        q: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        """Реальні Tempo-worklog-и за період зі станом звʼязку (екран `/tempo`).

        `jr_worklogs` ⋈ `jr_issues` (назва/ключ задачі) + похідний `is_linked`
        через EXISTS на `worklog_sync_tasks.target_id = jr_worklogs.id` (чи є
        наш WST-місток на цей worklog). Scoped по `worker_key` (чужі worklog-и не
        протікають, як `/tc-entries`). Фільтр `linked` (`all|linked|unlinked`),
        пошук `q` за **назвою** задачі (`ILIKE`), сорт `started_at` спадно,
        серверна пагінація; `total` — окремий COUNT за тим самим фільтром. Лише
        читання — без мутацій і нових колонок (D2).
        """
        period_lo = datetime.combine(date_from, time.min)
        period_hi = datetime.combine(date_to, time.max)

        # Звʼязок: чи існує WST-місток, що вказує на цей Tempo-worklog (target_id).
        linked_exists = (
            select(WorklogSyncTask.id)
            .where(WorklogSyncTask.target_id == JRWorklog.id)
            .exists()
        )

        conditions = [
            JRWorklog.jr_worker_key == worker_key,
            JRWorklog.started_at >= period_lo,
            JRWorklog.started_at <= period_hi,
        ]
        if linked == "linked":
            conditions.append(linked_exists)
        elif linked == "unlinked":
            conditions.append(~linked_exists)
        if q:
            conditions.append(JRIssue.name.ilike(f"%{q}%"))

        total = (
            await db.execute(
                select(func.count())
                .select_from(JRWorklog)
                .outerjoin(JRIssue, JRIssue.id == JRWorklog.jr_issues_id)
                .where(*conditions)
            )
        ).scalar_one()

        stmt = (
            select(
                JRWorklog.id,
                JRWorklog.description,
                JRWorklog.started_at,
                JRWorklog.duration,
                JRWorklog.jr_issues_id,
                JRIssue.key.label("issue_key"),
                JRIssue.name.label("issue_name"),
                linked_exists.label("is_linked"),
            )
            .select_from(JRWorklog)
            .outerjoin(JRIssue, JRIssue.id == JRWorklog.jr_issues_id)
            .where(*conditions)
            .order_by(JRWorklog.started_at.desc())
            .limit(limit)
            .offset(offset)
        )
        rows = (await db.execute(stmt)).mappings().all()
        return list(rows), int(total)

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
