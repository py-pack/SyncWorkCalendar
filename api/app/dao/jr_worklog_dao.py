from datetime import date, datetime, time
from sqlalchemy import select, and_, delete, func, update
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
        """Наявний Tempo-worklog для дедупу перед пушем — **fallback** за кортежем.

        Джерело правди про звʼязок — явний лінк `WorklogSyncTask.target_id`:
        лінкований WST (`created`/`updated`) **не** доходить сюди (виключений зі
        списку `_ACTIONABLE` у реконсиляції та guard-ом `noop` у `push_one`), тож
        повторного пушу немає. Цей метод — лише **fallback** для ще не лінкованих
        WST (`create`): шукає worklog, створений поза конвеєром / осиротілий, щоб
        привʼязати наявний `target_id` замість дубль-створення (capability
        `backend-auto-linking`, `harden-worklog-link` D4).

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
    async def find_duplicate_groups(
        cls,
        db: AsyncSession,
        worker_key: str | None,
        date_from: date,
        date_to: date,
    ) -> list[dict]:
        """Групи **дубльованих** Tempo-worklog-ів за період (capability `api-worklog-dedup`).

        Дублі — ≥2 рядки `jr_worklogs` з однаковим ключем дедупу
        `(jr_issues_id, jr_worker_key, started_at, duration)` — **тим самим**, що
        й `find_match`, тож «дублі» = те, що дедуп вважає одним worklog-ом (D1).
        Scoped по `worker_key` (без нього — порожній результат, бо видалення в
        Tempo персональне). Кожна група несе поля ключа, `issue_key`/`issue_name`
        (join `jr_issues`), `count` і перелік членів (`id`, `description`,
        `created_at`, `is_linked` — чи вказує на нього якийсь `WST.target_id`).
        """
        if not worker_key:
            return []

        period_lo = datetime.combine(date_from, time.min)
        period_hi = datetime.combine(date_to, time.max)

        # Ключі-дублі: групуємо за кортежем дедупу, лишаємо лише `count > 1`.
        grp = (
            select(
                JRWorklog.jr_issues_id.label("jr_issues_id"),
                JRWorklog.started_at.label("started_at"),
                JRWorklog.duration.label("duration"),
                func.count().label("cnt"),
            )
            .where(
                JRWorklog.jr_worker_key == worker_key,
                JRWorklog.started_at >= period_lo,
                JRWorklog.started_at <= period_hi,
            )
            .group_by(
                JRWorklog.jr_issues_id,
                JRWorklog.started_at,
                JRWorklog.duration,
            )
            .having(func.count() > 1)
            .subquery()
        )

        linked_exists = (
            select(WorklogSyncTask.id)
            .where(WorklogSyncTask.target_id == JRWorklog.id)
            .exists()
        )

        # Члени груп: усі worklog-и, чий ключ збігається з ключем-дублем.
        members_stmt = (
            select(
                JRWorklog.id,
                JRWorklog.description,
                JRWorklog.created_at,
                JRWorklog.jr_issues_id,
                JRWorklog.started_at,
                JRWorklog.duration,
                JRIssue.key.label("issue_key"),
                JRIssue.name.label("issue_name"),
                linked_exists.label("is_linked"),
            )
            .select_from(JRWorklog)
            .join(
                grp,
                and_(
                    JRWorklog.jr_issues_id == grp.c.jr_issues_id,
                    JRWorklog.started_at == grp.c.started_at,
                    JRWorklog.duration == grp.c.duration,
                ),
            )
            .outerjoin(JRIssue, JRIssue.id == JRWorklog.jr_issues_id)
            .where(JRWorklog.jr_worker_key == worker_key)
            .order_by(JRWorklog.started_at.desc(), JRWorklog.jr_issues_id, JRWorklog.id)
        )
        rows = (await db.execute(members_stmt)).mappings().all()

        # Згрупувати членів у пам'яті за ключем дедупу (порядок груп — за рядками).
        groups: dict[tuple, dict] = {}
        for r in rows:
            key = (r["jr_issues_id"], r["started_at"], r["duration"])
            group = groups.get(key)
            if group is None:
                group = {
                    "jr_issues_id": r["jr_issues_id"],
                    "started_at": r["started_at"],
                    "duration": r["duration"],
                    "issue_key": r["issue_key"],
                    "issue_name": r["issue_name"],
                    "members": [],
                }
                groups[key] = group
            group["members"].append(
                {
                    "id": r["id"],
                    "description": r["description"],
                    "created_at": r["created_at"],
                    "is_linked": bool(r["is_linked"]),
                }
            )

        result = list(groups.values())
        for g in result:
            g["count"] = len(g["members"])
        return result

    @classmethod
    async def linked_target_ids(
        cls, db: AsyncSession, ids: list[int]
    ) -> set[int]:
        """Підмножина `ids`, на яку вказує якийсь `WST.target_id` (вибір канонічного)."""
        if not ids:
            return set()
        rows = (
            await db.execute(
                select(WorklogSyncTask.target_id).where(
                    WorklogSyncTask.target_id.in_(ids)
                )
            )
        ).scalars().all()
        return {r for r in rows if r is not None}

    @staticmethod
    def choose_canonical(ids: list[int], linked_ids: set[int]) -> int:
        """«Лишити один» (D2): worklog із єдиним явним лінком, інакше найменший `id`.

        Якщо рівно один член групи має `WST.target_id` на себе — лишаємо його
        (джерело правди про звʼязок). Якщо таких немає або кілька — детермінований
        вибір за найменшим `id`.
        """
        linked = [i for i in ids if i in linked_ids]
        if len(linked) == 1:
            return linked[0]
        return min(ids)

    @classmethod
    async def get_by_ids(
        cls, db: AsyncSession, ids: list[int]
    ) -> list[JRWorklog]:
        """Наявні `jr_worklogs` за переліком `id` (фільтр «що реально існує»)."""
        if not ids:
            return []
        rows = (
            await db.execute(select(cls.model).where(cls.model.id.in_(ids)))
        ).scalars().all()
        return list(rows)

    @classmethod
    async def repoint_links(
        cls, db: AsyncSession, *, from_id: int, to_id: int
    ) -> int:
        """Перенацілити всі `WST.target_id == from_id` на `to_id` (до видалення).

        Зберігає звʼязок календаря/конвеєра, коли видаляємо worklog, на який
        вказував WST (D3). Повертає к-сть оновлених WST.
        """
        res = await db.execute(
            update(WorklogSyncTask)
            .where(WorklogSyncTask.target_id == from_id)
            .values(target_id=to_id)
        )
        return res.rowcount or 0

    @classmethod
    async def delete_by_ids(cls, db: AsyncSession, ids: list[int]) -> int:
        """Видалити рядки `jr_worklogs` за `id` (локальне дзеркало; D3)."""
        if not ids:
            return 0
        res = await db.execute(delete(cls.model).where(cls.model.id.in_(ids)))
        return res.rowcount or 0

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
