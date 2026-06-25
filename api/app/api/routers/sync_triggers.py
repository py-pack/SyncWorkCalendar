"""Sync-trigger endpoints: REST wrappers around the existing tasks.

Each endpoint is wrapped in :func:`app.api.jobs_wrapper.run_job` so every
invocation lands in ``api_jobs`` and goes through the
``running -> needs_verification | failed`` lifecycle. ``?background=true``
defers execution to ``BackgroundTasks`` and returns ``202 Accepted`` with the
job id; the caller polls ``GET /api-jobs/{id}``.
"""

from datetime import date, datetime, time
from typing import Any, Awaitable, Callable

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Body,
    Depends,
    HTTPException,
    Query,
    status,
)
from fastapi.responses import JSONResponse
from sqlalchemy import func, select

from app.api.deps import CurrentUser, get_current_user
from app.api.jobs_wrapper import create_job, run_job
from app.api.period import current_month
from app.api.schemas.sync_triggers import IssuesKeysBody, PeriodBody
from app.core.db_helper import async_session_maker
from app.dao import APIJobDAO
from app.models import (
    JRIssue,
    JRProject,
    JRWorklog,
    StatusTaskEnum,
    TCEntry,
    TCProject,
    WorklogSyncTask,
)
from app.tasks import celery_tasks
from app.tasks.jira_update_task import UpdateJiraTask
from app.tasks.time_camp_update_task import TimeCampUpdateTask
from app.tasks.worllog_sync_task import WorllogSyncTask


router = APIRouter()


_MISSING_WORKER_KEY = "user has no worker_key configured"
_QUEUE_UNAVAILABLE = "task queue unavailable"


async def _count(stmt) -> int:
    async with async_session_maker() as session:
        return int((await session.execute(stmt)).scalar_one())


async def _execute(
    *,
    trigger_name: str,
    payload: dict[str, Any] | None,
    created_by: str,
    background: bool,
    bg_tasks: BackgroundTasks,
    work: Callable[[], Awaitable[dict[str, Any] | None]],
    enqueue: Callable[[str], Any] | None = None,
) -> JSONResponse:
    # Фоновий режим (`?background=true`): важкі тригери йдуть у **тривку чергу**
    # Celery (`enqueue`), а не в ефемерні FastAPI BackgroundTasks (живуть лише в
    # процесі api й не переживають рестарт). `api_jobs`-рядок створює тригер, щоб
    # одразу повернути `job_id`; воркер закриває його (capability `async-task-queue`).
    if background and enqueue is not None:
        job_id = await create_job(
            trigger_name=trigger_name, payload=payload, created_by=created_by
        )
        try:
            enqueue(str(job_id))
        except Exception as exc:
            # Брокер недоступний → не «з'їдаємо» завдання тихо: позначаємо рядок
            # failed і явно віддаємо помилку викликачеві (spec async-task-queue).
            async with async_session_maker() as session:
                await APIJobDAO.mark_failed(
                    session, job_id, f"enqueue failed: {exc}"
                )
                await session.commit()
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=_QUEUE_UNAVAILABLE,
            )
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={"job_id": str(job_id), "status": "queued"},
        )

    if background:
        # Тригери без Celery-еквіваленту (точковий jr/issues, legacy WST-кроки) —
        # лишаються на BackgroundTasks (зворотна сумісність).
        job_id = await create_job(
            trigger_name=trigger_name, payload=payload, created_by=created_by
        )

        async def _bg() -> None:
            try:
                result = await work()
            except Exception as exc:
                async with async_session_maker() as session:
                    await APIJobDAO.mark_failed(session, job_id, str(exc))
                    await session.commit()
                return
            async with async_session_maker() as session:
                await APIJobDAO.mark_needs_verification(
                    session, job_id, result
                )
                await session.commit()

        bg_tasks.add_task(_bg)
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={"job_id": str(job_id), "status": "running"},
        )

    async with run_job(
        trigger_name=trigger_name, payload=payload, created_by=created_by
    ) as ctx:
        ctx.result = await work()
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "job_id": str(ctx.job_id),
            "status": "needs_verification",
            "result": ctx.result,
        },
    )


# ---- task helpers --------------------------------------------------------


async def _do_tc_projects() -> dict[str, Any]:
    before = await _count(select(func.count()).select_from(TCProject))
    await TimeCampUpdateTask().update_project()
    after = await _count(select(func.count()).select_from(TCProject))
    return {"total": after, "delta": after - before}


async def _do_tc_entries(payload: dict[str, Any]) -> dict[str, Any]:
    period_lo = datetime.combine(
        date.fromisoformat(payload["start"]), time.min
    )
    period_hi = datetime.combine(date.fromisoformat(payload["end"]), time.max)
    where = (TCEntry.start_at >= period_lo) & (TCEntry.start_at <= period_hi)
    before = await _count(
        select(func.count()).select_from(TCEntry).where(where)
    )
    await TimeCampUpdateTask().update_entries(period_lo, period_hi)
    after = await _count(
        select(func.count()).select_from(TCEntry).where(where)
    )
    return {"total": after, "delta": after - before}


async def _do_jr_projects() -> dict[str, Any]:
    before = await _count(select(func.count()).select_from(JRProject))
    await UpdateJiraTask().update_all_projects()
    after = await _count(select(func.count()).select_from(JRProject))
    return {"total": after, "delta": after - before}


async def _do_jr_issues(payload: dict[str, Any]) -> dict[str, Any]:
    keys = list(payload.get("keys") or [])
    await UpdateJiraTask().update_jira_issues(keys)
    after = await _count(
        select(func.count()).select_from(JRIssue).where(JRIssue.key.in_(keys))
    )
    return {"requested": len(keys), "present": after}


async def _do_jr_issues_all(payload: dict[str, Any] | None) -> dict[str, Any]:
    updated_from = payload.get("start") if payload else None
    updated_to = payload.get("end") if payload else None
    before = await _count(select(func.count()).select_from(JRIssue))
    synced = await UpdateJiraTask().update_issues_for_watched_projects(
        updated_from=updated_from, updated_to=updated_to
    )
    after = await _count(select(func.count()).select_from(JRIssue))
    return {"synced": synced, "total": after, "delta": after - before}


async def _do_jr_worklogs(payload: dict[str, Any]) -> dict[str, Any]:
    period_lo = datetime.combine(
        date.fromisoformat(payload["start"]), time.min
    )
    period_hi = datetime.combine(date.fromisoformat(payload["end"]), time.max)
    worker = payload["worker_key"]
    where = (JRWorklog.started_at >= period_lo) & (
        JRWorklog.started_at <= period_hi
    )
    before = await _count(
        select(func.count()).select_from(JRWorklog).where(where)
    )
    await UpdateJiraTask().update_worklog(period_lo, period_hi, worker=worker)
    after = await _count(
        select(func.count()).select_from(JRWorklog).where(where)
    )
    return {"worklogs_synced": after - before, "total_in_period": after}


async def _do_wst_prepare(payload: dict[str, Any]) -> dict[str, Any]:
    period_lo = datetime.combine(
        date.fromisoformat(payload["start"]), time.min
    )
    period_hi = datetime.combine(date.fromisoformat(payload["end"]), time.max)
    where = (WorklogSyncTask.started_at >= period_lo) & (
        WorklogSyncTask.started_at <= period_hi
    )
    before = await _count(
        select(func.count()).select_from(WorklogSyncTask).where(where)
    )
    await WorllogSyncTask.create_task_for_sync(period_lo, period_hi)
    after = await _count(
        select(func.count()).select_from(WorklogSyncTask).where(where)
    )
    return {"created": after - before, "total_in_period": after}


async def _do_wst_resolve(payload: dict[str, Any]) -> dict[str, Any]:
    period_lo = datetime.combine(
        date.fromisoformat(payload["start"]), time.min
    )
    period_hi = datetime.combine(date.fromisoformat(payload["end"]), time.max)
    where_create = (
        (WorklogSyncTask.started_at >= period_lo)
        & (WorklogSyncTask.started_at <= period_hi)
        & (WorklogSyncTask.status == StatusTaskEnum.create)
    )
    await WorllogSyncTask.before_create(period_lo, period_hi)
    resolved = await _count(
        select(func.count()).select_from(WorklogSyncTask).where(where_create)
    )
    return {"resolved": resolved}


async def _do_wst_push(payload: dict[str, Any]) -> dict[str, Any]:
    period_lo = datetime.combine(
        date.fromisoformat(payload["start"]), time.min
    )
    period_hi = datetime.combine(date.fromisoformat(payload["end"]), time.max)
    worker = payload["worker_key"]
    where_created = (
        (WorklogSyncTask.started_at >= period_lo)
        & (WorklogSyncTask.started_at <= period_hi)
        & (WorklogSyncTask.status == StatusTaskEnum.created)
    )
    before = await _count(
        select(func.count()).select_from(WorklogSyncTask).where(where_created)
    )
    await WorllogSyncTask().create_worklogs(
        period_lo, period_hi, worker=worker
    )
    after = await _count(
        select(func.count()).select_from(WorklogSyncTask).where(where_created)
    )
    return {"pushed": after - before, "total_created_in_period": after}


# ---- endpoints -----------------------------------------------------------


@router.post("/timecamp/projects")
async def sync_timecamp_projects(
    background: bool = Query(default=False),
    current: CurrentUser = Depends(get_current_user),
    bg_tasks: BackgroundTasks = BackgroundTasks(),
) -> JSONResponse:
    return await _execute(
        trigger_name="sync.timecamp.projects",
        payload=None,
        created_by=current.username,
        background=background,
        bg_tasks=bg_tasks,
        work=_do_tc_projects,
        enqueue=lambda jid: celery_tasks.sync_timecamp_projects.delay(
            created_by=current.username, job_id=jid
        ),
    )


@router.post("/timecamp/entries")
async def sync_timecamp_entries(
    body: PeriodBody = Body(...),
    background: bool = Query(default=False),
    current: CurrentUser = Depends(get_current_user),
    bg_tasks: BackgroundTasks = BackgroundTasks(),
) -> JSONResponse:
    payload = {"start": body.start.isoformat(), "end": body.end.isoformat()}
    return await _execute(
        trigger_name="sync.timecamp.entries",
        payload=payload,
        created_by=current.username,
        background=background,
        bg_tasks=bg_tasks,
        work=lambda: _do_tc_entries(payload),
        enqueue=lambda jid: celery_tasks.sync_timecamp_entries.delay(
            payload["start"],
            payload["end"],
            created_by=current.username,
            job_id=jid,
        ),
    )


@router.post("/jira/projects")
async def sync_jira_projects(
    background: bool = Query(default=False),
    current: CurrentUser = Depends(get_current_user),
    bg_tasks: BackgroundTasks = BackgroundTasks(),
) -> JSONResponse:
    return await _execute(
        trigger_name="sync.jira.projects",
        payload=None,
        created_by=current.username,
        background=background,
        bg_tasks=bg_tasks,
        work=_do_jr_projects,
        enqueue=lambda jid: celery_tasks.sync_jira_projects.delay(
            created_by=current.username, job_id=jid
        ),
    )


@router.post("/jira/issues")
async def sync_jira_issues(
    body: IssuesKeysBody = Body(...),
    background: bool = Query(default=False),
    current: CurrentUser = Depends(get_current_user),
    bg_tasks: BackgroundTasks = BackgroundTasks(),
) -> JSONResponse:
    # Validation runs before the wrapper (api-sync-triggers ``Empty keys array``).
    if not body.keys:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="keys must be non-empty",
        )
    payload = {"keys": body.keys}
    return await _execute(
        trigger_name="sync.jira.issues",
        payload=payload,
        created_by=current.username,
        background=background,
        bg_tasks=bg_tasks,
        work=lambda: _do_jr_issues(payload),
    )


@router.post("/jira/issues-all")
async def sync_jira_issues_all(
    body: PeriodBody | None = Body(default=None),
    background: bool = Query(default=False),
    current: CurrentUser = Depends(get_current_user),
    bg_tasks: BackgroundTasks = BackgroundTasks(),
) -> JSONResponse:
    """Витяг задач відстежуваних проектів (`is_watched`) у `jr_issues`.

    На відміну від `/jira/issues` (точково за ключами) і `/jira/worklogs` (лише
    задачі з worklog-ами), тягне задачі watched-проектів незалежно від assignee.
    За наявності тіла `{start, end}` обмежує **періодом активності** (`updated`);
    без тіла — усі задачі.
    """
    payload = (
        {"start": body.start.isoformat(), "end": body.end.isoformat()}
        if body
        else None
    )
    return await _execute(
        trigger_name="sync.jira.issues-all",
        payload=payload,
        created_by=current.username,
        background=background,
        bg_tasks=bg_tasks,
        work=lambda: _do_jr_issues_all(payload),
        enqueue=lambda jid: celery_tasks.sync_jira_issues_all.delay(
            payload["start"] if payload else None,
            payload["end"] if payload else None,
            created_by=current.username,
            job_id=jid,
        ),
    )


@router.post("/jira/worklogs")
async def sync_jira_worklogs(
    body: PeriodBody = Body(...),
    background: bool = Query(default=False),
    current: CurrentUser = Depends(get_current_user),
    bg_tasks: BackgroundTasks = BackgroundTasks(),
) -> JSONResponse:
    if not current.worker_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=_MISSING_WORKER_KEY
        )
    payload = {
        "start": body.start.isoformat(),
        "end": body.end.isoformat(),
        "worker_key": current.worker_key,
    }
    return await _execute(
        trigger_name="sync.jira.worklogs",
        payload=payload,
        created_by=current.username,
        background=background,
        bg_tasks=bg_tasks,
        work=lambda: _do_jr_worklogs(payload),
        enqueue=lambda jid: celery_tasks.sync_tempo_worklogs.delay(
            payload["start"],
            payload["end"],
            payload["worker_key"],
            created_by=current.username,
            job_id=jid,
        ),
    )


@router.post("/worklog-tasks/prepare")
async def sync_wst_prepare(
    body: PeriodBody = Body(...),
    background: bool = Query(default=False),
    current: CurrentUser = Depends(get_current_user),
    bg_tasks: BackgroundTasks = BackgroundTasks(),
) -> JSONResponse:
    payload = {"start": body.start.isoformat(), "end": body.end.isoformat()}
    return await _execute(
        trigger_name="sync.worklog-tasks.prepare",
        payload=payload,
        created_by=current.username,
        background=background,
        bg_tasks=bg_tasks,
        work=lambda: _do_wst_prepare(payload),
    )


@router.post("/worklog-tasks/resolve-issues")
async def sync_wst_resolve(
    body: PeriodBody = Body(...),
    background: bool = Query(default=False),
    current: CurrentUser = Depends(get_current_user),
    bg_tasks: BackgroundTasks = BackgroundTasks(),
) -> JSONResponse:
    payload = {"start": body.start.isoformat(), "end": body.end.isoformat()}
    return await _execute(
        trigger_name="sync.worklog-tasks.resolve-issues",
        payload=payload,
        created_by=current.username,
        background=background,
        bg_tasks=bg_tasks,
        work=lambda: _do_wst_resolve(payload),
    )


@router.post("/worklog-tasks/push-to-tempo")
async def sync_wst_push(
    body: PeriodBody = Body(...),
    background: bool = Query(default=False),
    current: CurrentUser = Depends(get_current_user),
    bg_tasks: BackgroundTasks = BackgroundTasks(),
) -> JSONResponse:
    if not current.worker_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=_MISSING_WORKER_KEY
        )
    payload = {
        "start": body.start.isoformat(),
        "end": body.end.isoformat(),
        "worker_key": current.worker_key,
    }
    return await _execute(
        trigger_name="sync.worklog-tasks.push-to-tempo",
        payload=payload,
        created_by=current.username,
        background=background,
        bg_tasks=bg_tasks,
        work=lambda: _do_wst_push(payload),
    )


@router.post("/reconcile-links")
async def sync_reconcile_links(
    body: PeriodBody | None = Body(default=None),
    current: CurrentUser = Depends(get_current_user),
) -> JSONResponse:
    """Поставити в чергу реконсиляцію лінків TimeCamp↔Tempo для свого `worker_key`.

    Серверний еквівалент кнопки «звʼязати/синхронізувати все»: **лише** enqueue,
    а виконання й `api_jobs`-аудит відбуваються у воркері (capability
    `async-task-queue`). Без `worker_key` у токені — `400` до постановки. Без
    тіла — дефолтний останній період (поточний місяць). Реальний пуш у Tempo
    усередині реконсиляції гейтиться per-user `auto_push_tempo`.
    """
    if not current.worker_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=_MISSING_WORKER_KEY
        )

    if body is not None:
        start_iso, end_iso = body.start.isoformat(), body.end.isoformat()
    else:
        first, last = current_month()
        start_iso, end_iso = first.isoformat(), last.isoformat()

    payload = {
        "start": start_iso,
        "end": end_iso,
        "worker_key": current.worker_key,
    }
    job_id = await create_job(
        trigger_name="sync.reconcile-links",
        payload=payload,
        created_by=current.username,
    )
    try:
        celery_tasks.reconcile_links.delay(
            start_iso,
            end_iso,
            current.worker_key,
            created_by=current.username,
            job_id=str(job_id),
        )
    except Exception as exc:
        async with async_session_maker() as session:
            await APIJobDAO.mark_failed(
                session, job_id, f"enqueue failed: {exc}"
            )
            await session.commit()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=_QUEUE_UNAVAILABLE,
        )

    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={"job_id": str(job_id), "status": "queued"},
    )
