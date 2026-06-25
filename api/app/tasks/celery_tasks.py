"""Celery-таски: тонкі обгортки над наявними async-методами + beat-диспетчери.

Таски не дублюють логіку (D3) — викликають корутини `TimeCampUpdateTask`,
`UpdateJiraTask`, `ReconcileLinksTask` через місток `run_audited_task`
(свіжий engine + `api_jobs`-аудит). Диспетчери (`beat.*`) самі НЕ роблять важкої
роботи: вони читають активних користувачів, поважають їхні `sync_prefs` (D9) і
ставлять у чергу глобальні/per-user таски.
"""

from datetime import date, datetime, time, timedelta

from app.celery_app import celery_app
from app.core import get_async_asession
from app.core.utils.sync_prefs import normalize_sync_prefs
from app.dao import APIUserDAO
from app.tasks.celery_bridge import run_async, run_audited_task
from app.tasks.jira_update_task import UpdateJiraTask
from app.tasks.reconcile_task import ReconcileLinksTask
from app.tasks.time_camp_update_task import TimeCampUpdateTask


# ---- хелпери періоду ------------------------------------------------------


def _lo(iso: str) -> datetime:
    return datetime.combine(date.fromisoformat(iso), time.min)


def _hi(iso: str) -> datetime:
    return datetime.combine(date.fromisoformat(iso), time.max)


def _default_period() -> tuple[str, str]:
    """Дефолтний період планових витягів — поточний місяць (як read-ендпоінти)."""
    today = date.today()
    first = today.replace(day=1)
    next_first = (first.replace(day=28) + timedelta(days=4)).replace(day=1)
    last = next_first - timedelta(days=1)
    return first.isoformat(), last.isoformat()


# ---- worker-таски (виконують роботу під api_jobs-аудитом) -----------------


@celery_app.task(name="sync.timecamp.projects")
def sync_timecamp_projects(
    created_by: str = "beat", job_id: str | None = None
) -> str:
    async def work() -> dict:
        await TimeCampUpdateTask().update_project()
        return {"task": "timecamp.projects"}

    return run_audited_task(
        trigger_name="sync.timecamp.projects",
        created_by=created_by,
        work=work,
        job_id=job_id,
    )


@celery_app.task(name="sync.timecamp.entries")
def sync_timecamp_entries(
    start: str, end: str, created_by: str = "beat", job_id: str | None = None
) -> str:
    payload = {"start": start, "end": end}

    async def work() -> dict:
        await TimeCampUpdateTask().update_entries(_lo(start), _hi(end))
        return {"task": "timecamp.entries", "period": [start, end]}

    return run_audited_task(
        trigger_name="sync.timecamp.entries",
        created_by=created_by,
        payload=payload,
        work=work,
        job_id=job_id,
    )


@celery_app.task(name="sync.jira.projects")
def sync_jira_projects(
    created_by: str = "beat", job_id: str | None = None
) -> str:
    async def work() -> dict:
        await UpdateJiraTask().update_all_projects()
        return {"task": "jira.projects"}

    return run_audited_task(
        trigger_name="sync.jira.projects",
        created_by=created_by,
        work=work,
        job_id=job_id,
    )


@celery_app.task(name="sync.jira.issues-all")
def sync_jira_issues_all(
    start: str | None = None,
    end: str | None = None,
    created_by: str = "beat",
    job_id: str | None = None,
) -> str:
    payload = {"start": start, "end": end} if start else None

    async def work() -> dict:
        synced = await UpdateJiraTask().update_issues_for_watched_projects(
            updated_from=start, updated_to=end
        )
        return {"task": "jira.issues-all", "synced": synced}

    return run_audited_task(
        trigger_name="sync.jira.issues-all",
        created_by=created_by,
        payload=payload,
        work=work,
        job_id=job_id,
    )


@celery_app.task(name="sync.jira.worklogs")
def sync_tempo_worklogs(
    start: str,
    end: str,
    worker_key: str,
    created_by: str = "beat",
    job_id: str | None = None,
) -> str:
    payload = {"start": start, "end": end, "worker_key": worker_key}

    async def work() -> dict:
        await UpdateJiraTask().update_worklog(
            _lo(start), _hi(end), worker=worker_key
        )
        return {
            "task": "jira.worklogs",
            "period": [start, end],
            "worker_key": worker_key,
        }

    return run_audited_task(
        trigger_name="sync.jira.worklogs",
        created_by=created_by,
        payload=payload,
        work=work,
        job_id=job_id,
    )


@celery_app.task(name="sync.reconcile-links")
def reconcile_links(
    start: str,
    end: str,
    worker_key: str,
    created_by: str = "beat",
    job_id: str | None = None,
) -> str:
    payload = {"start": start, "end": end, "worker_key": worker_key}

    async def work() -> dict:
        return await ReconcileLinksTask().run(_lo(start), _hi(end), worker_key)

    return run_audited_task(
        trigger_name="sync.reconcile-links",
        created_by=created_by,
        payload=payload,
        work=work,
        job_id=job_id,
    )


# ---- beat-диспетчери (ставлять у чергу, поважаючи sync_prefs) --------------


async def _load_users_prefs() -> list[dict]:
    """Активні користувачі з worker_key + нормалізовані sync_prefs (для beat)."""
    async with get_async_asession() as db:
        users = await APIUserDAO.list_active_with_worker(db)
        return [
            {
                "worker_key": u.worker_key,
                "username": u.username,
                "prefs": normalize_sync_prefs(u.sync_prefs),
            }
            for u in users
        ]


@celery_app.task(name="beat.pull_timecamp_jira")
def beat_pull_timecamp_jira() -> dict:
    """`01:00`: глобальні витяги TimeCamp/Jira (раз) + per-user реконсиляція."""
    users = run_async(_load_users_prefs)
    start, end = _default_period()

    # Глобальні дані (один TC/Jira-токен на всіх) — раз за тік, якщо хоч один
    # користувач увімкнув відповідний автосинк (opt-in).
    if any(u["prefs"]["auto_timecamp_pull"] for u in users):
        sync_timecamp_projects.delay()
        sync_timecamp_entries.delay(start, end)
    if any(u["prefs"]["auto_jira_pull"] for u in users):
        sync_jira_projects.delay()
        sync_jira_issues_all.delay(start, end)

    # Реконсиляція — per-user, лише за ввімкненого auto_linking.
    queued = 0
    for u in users:
        if u["prefs"]["auto_linking"]:
            reconcile_links.delay(start, end, u["worker_key"], u["username"])
            queued += 1
    return {"users": len(users), "reconcile_queued": queued}


@celery_app.task(name="beat.pull_tempo")
def beat_pull_tempo() -> dict:
    """`01:30`: per-user витяг Tempo-worklog-ів + реконсиляція (за прапорами)."""
    users = run_async(_load_users_prefs)
    start, end = _default_period()

    tempo_queued = reconcile_queued = 0
    for u in users:
        if u["prefs"]["auto_tempo_pull"]:
            sync_tempo_worklogs.delay(
                start, end, u["worker_key"], u["username"]
            )
            tempo_queued += 1
        if u["prefs"]["auto_linking"]:
            reconcile_links.delay(start, end, u["worker_key"], u["username"])
            reconcile_queued += 1
    return {
        "users": len(users),
        "tempo_queued": tempo_queued,
        "reconcile_queued": reconcile_queued,
    }
