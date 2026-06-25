"""Авто-реконсиляція лінків TimeCamp↔Tempo (capability `backend-auto-linking`).

Ідемпотентна задача `reconcile_links(period, worker_key)`, що зводить
`worklog_sync_tasks` у відповідність до поточних TimeCamp-записів періоду й
доводить метч до кінцевого стану в Tempo. Закриває три розриви наявного
ручного конвеєра (`create_task_for_sync → before_create → create_worklogs`):

1. **Перелінк на зміну опису** — наявний WST перенацілюється на нову задачу,
   якщо опис почав матчити інший ключ; якщо матч зник — звʼязок лишається
   (ніколи не відлінковуємо авто, D4).
2. **Дедуп проти `jr_worklogs`** — перед пушем звіряємо кандидата з реальними
   Tempo-worklog-ами; збіг → `target_id` без повторного HTTP (D5).
3. **Update-flow** — вже запушений запис, чий контент/час змінилися, проходить
   `created → pre_update → update → updated` через Tempo `PUT` (D6).

Пуш/оновлення в Tempo гейтиться per-user прапором `auto_push_tempo`: за
вимкненого реконсиляція оновлює лише звʼязок, але нічого не пише в Tempo (D7).
"""

from datetime import datetime

from app.config import settings
from app.core import get_async_asession
from app.core.utils.sync_prefs import normalize_sync_prefs
from app.dao import (
    APIUserDAO,
    JRIssuesDAO,
    JRWorklogDAO,
    TCEntriesDAO,
    WorklogSyncTaskDAO,
)
from app.models import StatusTaskEnum, WorklogSyncTask
from app.services.jira import JiraService
from app.tasks.jira_update_task import UpdateJiraTask

# Статуси, з якими WST ще не доведений до кінця (потребує резолву issue_id і дії).
_ACTIONABLE = (
    StatusTaskEnum.pre_create,
    StatusTaskEnum.create,
    StatusTaskEnum.pre_update,
    StatusTaskEnum.update,
)
# Статуси, у яких worklog уже існує в Tempo (є target_id).
_PUSHED = (StatusTaskEnum.created, StatusTaskEnum.updated)


def _naive_utc(dt: datetime | None) -> datetime | None:
    """Звести datetime до naive UTC wall-clock для коректного порівняння.

    `WorklogSyncTask.started_at` — `timestamptz` (asyncpg віддає aware-UTC), а
    кандидатів `started_at` походить із `TCEntry.start_at` (`timestamp` без tz →
    naive). Пряме `aware != naive` у Python завжди True (не кидає виняток), що
    робило б кожен уже-`created` запис «зміненим» і плодило б зайві Tempo-PUT на
    кожному проході. Усе в системі — UTC, тож зрізаємо tzinfo і порівнюємо
    wall-clock (зберігає ідемпотентність реконсиляції)."""
    if dt is not None and dt.tzinfo is not None:
        return dt.replace(tzinfo=None)
    return dt


class ReconcileLinksTask:
    def __init__(self):
        self.jira_client = JiraService(settings.jira.token)

    async def run(
        self,
        start_date: datetime,
        end_date: datetime,
        worker_key: str,
    ) -> dict:
        # Прапор пушу читаємо з sync_prefs власника (opt-in; дефолт false).
        async with get_async_asession() as db:
            user = await APIUserDAO.get_by_worker_key(db, worker_key)
            auto_push = normalize_sync_prefs(
                user.sync_prefs if user else None
            )["auto_push_tempo"]

        stats = await self._upsert_links(start_date, end_date, worker_key)
        await self._resolve_issue_ids(start_date, end_date, worker_key)

        pushed = {"created": 0, "deduped": 0, "updated": 0}
        if auto_push:
            pushed = await self._push(start_date, end_date, worker_key)

        return {**stats, **pushed, "auto_push": auto_push}

    async def _upsert_links(
        self, start_date: datetime, end_date: datetime, worker_key: str
    ) -> dict:
        """Створити/перелінкувати/оновити WST за поточними матчами (без Tempo)."""
        created = relinked = remarked = 0
        async with get_async_asession() as db:
            candidates = await TCEntriesDAO().get_match_candidates(
                db, worker_key, start_date, end_date
            )
            source_ids = [c.source_id for c in candidates]
            existing = await WorklogSyncTaskDAO.get_by_source_ids(
                db, source_ids, worker_key
            )

            for c in candidates:
                wst = existing.get(c.source_id)
                if wst is None:
                    db.add(WorklogSyncTask.create(**c.model_dump()))
                    created += 1
                    continue

                relink = wst.issue_key != c.issue_key
                fields_changed = (
                    wst.content != c.content
                    or _naive_utc(wst.started_at) != _naive_utc(c.started_at)
                    or wst.time_spent != c.time_spent
                )

                if wst.status in _PUSHED:
                    # Уже в Tempo: зміна → позначаємо на оновлення (target_id
                    # лишаємо, видалення поза скоупом). Без змін → no-op.
                    if relink or fields_changed:
                        wst.issue_key = c.issue_key
                        wst.content = c.content
                        wst.started_at = c.started_at
                        wst.time_spent = c.time_spent
                        if relink:
                            wst.issue_id = None  # форс-перерезолв
                        wst.status = StatusTaskEnum.pre_update
                        remarked += 1
                    if relink:
                        relinked += 1
                else:
                    # Ще не запушений: освіжаємо поля під поточний запис.
                    if relink:
                        wst.issue_key = c.issue_key
                        wst.issue_id = None
                        relinked += 1
                    wst.content = c.content
                    wst.started_at = c.started_at
                    wst.time_spent = c.time_spent

            await db.commit()
        return {"created": created, "relinked": relinked, "remarked": remarked}

    async def _resolve_issue_ids(
        self, start_date: datetime, end_date: datetime, worker_key: str
    ) -> None:
        """Підтягнути відсутні Jira-задачі й проставити `issue_id`; pre_create→create."""
        # 1) Зібрати ключі actionable-WST і дотягнути відсутні задачі.
        async with get_async_asession() as db:
            tasks = await self._actionable_tasks(
                db, start_date, end_date, worker_key
            )
            wanted_keys = {t.issue_key for t in tasks if t.issue_key}
            if not wanted_keys:
                return
            present = await JRIssuesDAO.get_in_keys(db, wanted_keys)
            missing = wanted_keys - {row.key for row in present}

        if missing:
            await UpdateJiraTask().update_jira_issues(missing)

        # 2) Проставити issue_id з мапи ключ→id; перевести pre_create у create.
        async with get_async_asession() as db:
            tasks = await self._actionable_tasks(
                db, start_date, end_date, worker_key
            )
            keys = {t.issue_key for t in tasks if t.issue_key}
            id_by_key = {
                row.key: row.id
                for row in await JRIssuesDAO.get_in_keys(db, keys)
            }
            for t in tasks:
                t.issue_id = id_by_key.get(t.issue_key)
                if t.status == StatusTaskEnum.pre_create:
                    t.status = StatusTaskEnum.create
            await db.commit()

    async def _push(
        self, start_date: datetime, end_date: datetime, worker_key: str
    ) -> dict:
        """Створити/оновити Tempo-worklog-и; дедуп проти `jr_worklogs`."""
        created = deduped = updated = 0
        async with get_async_asession() as db:
            tasks = await self._actionable_tasks(
                db, start_date, end_date, worker_key
            )
            for t in tasks:
                if t.issue_id is None:
                    continue  # ключ не зарезолвився — пропускаємо до наступного проходу

                if t.status == StatusTaskEnum.create:
                    match = await JRWorklogDAO.find_match(
                        db,
                        jr_issues_id=int(t.issue_id),
                        jr_worker_key=worker_key,
                        started_at=t.started_at,
                        duration=t.time_spent,
                    )
                    if match is not None:
                        # Дедуп: worklog уже в Tempo → лінкуємо без HTTP-пушу.
                        t.target_id = match.id
                        t.status = StatusTaskEnum.created
                        deduped += 1
                    else:
                        result = self.jira_client.create_worklog(
                            worker_key,
                            int(t.issue_id),
                            t.content,
                            t.started_at,
                            t.time_spent,
                        )
                        t.target_id = result.get("originId")
                        t.status = StatusTaskEnum.created
                        created += 1
                    await db.commit()

                elif t.status == StatusTaskEnum.pre_update and t.target_id:
                    t.status = StatusTaskEnum.update
                    self.jira_client.update_worklog(
                        int(t.target_id),
                        worker_key,
                        int(t.issue_id),
                        t.content,
                        t.started_at,
                        t.time_spent,
                    )
                    t.status = StatusTaskEnum.updated
                    updated += 1
                    await db.commit()

        return {"created": created, "deduped": deduped, "updated": updated}

    @staticmethod
    async def _actionable_tasks(
        db, start_date: datetime, end_date: datetime, worker_key: str
    ) -> list[WorklogSyncTask]:
        """WST періоду для одного worker-а у незавершених статусах (`_ACTIONABLE`)."""
        all_in_period = await WorklogSyncTaskDAO.get_by_period_and_status(
            db, start_date, end_date, status=None
        )
        return [
            t
            for t in all_in_period
            if t.worker_key == worker_key and t.status in _ACTIONABLE
        ]
