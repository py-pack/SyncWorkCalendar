from datetime import date
from typing import Literal, cast

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_current_user, get_db
from app.api.jobs_wrapper import run_job
from app.api.period import current_month as _current_month, period_or_400 as _period_or_400
from app.api.schemas.sync_status import (
    JRWorklogItem,
    JRWorklogsResponse,
    TCEntriesResponse,
    TCEntryItem,
    UntrackedEntry,
    WorklogDedupRequest,
    WorklogDedupResponse,
    WorklogDuplicateGroup,
    WorklogDuplicateMember,
    WorklogDuplicatesResponse,
    WorklogSyncTaskItem,
    WorklogSyncTasksResponse,
)
from app.dao import JRWorklogDAO, TCEntriesDAO
from app.models import JRIssue, StatusTaskEnum, TCEntry, TCProject, WorklogSyncTask
from app.tasks.dedup_task import WorklogDedupTask


router = APIRouter()

_MISSING_WORKER_KEY = "user has no worker_key configured"


@router.get("/worklog-sync-tasks", response_model=WorklogSyncTasksResponse)
async def list_worklog_sync_tasks(
    start: date = Query(...),
    end: date = Query(...),
    status_filter: Literal[
        "pre_create", "create", "created", "pre_update", "update", "updated", "sync"
    ]
    | None = Query(default=None, alias="status"),
    synced: Literal["all", "synced", "unsynced"] = Query(default="all"),
    q: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WorklogSyncTasksResponse:
    """Конвеєр worklog-sync-tasks за період зі зведенням, фільтрами й пагінацією.

    `summary` рахується по **всьому** періоду (повна картина статусів), а `items`
    застосовують фільтри сторінки: точний `status`, стан синку `synced`
    (`target_id IS NOT NULL`) і пошук `q` за **назвою** задачі (`jr_issues`).
    `total` відображає відфільтровану кількість.
    """
    period_lo, period_hi = _period_or_400(start, end)

    summary_stmt = (
        select(WorklogSyncTask.status, func.count())
        .where(WorklogSyncTask.started_at >= period_lo, WorklogSyncTask.started_at <= period_hi)
        .group_by(WorklogSyncTask.status)
    )
    summary_rows = (await db.execute(summary_stmt)).all()
    summary = {member.value: 0 for member in StatusTaskEnum}
    for status_enum, cnt in summary_rows:
        summary[status_enum.value] = int(cnt)

    # Фільтри сторінки (status/synced/q) + join jr_issues для issue_name/пошуку.
    conditions = [
        WorklogSyncTask.started_at >= period_lo,
        WorklogSyncTask.started_at <= period_hi,
    ]
    if status_filter is not None:
        conditions.append(WorklogSyncTask.status == StatusTaskEnum(status_filter))
    if synced == "synced":
        conditions.append(WorklogSyncTask.target_id.is_not(None))
    elif synced == "unsynced":
        conditions.append(WorklogSyncTask.target_id.is_(None))
    if q:
        conditions.append(JRIssue.name.ilike(f"%{q}%"))

    total = (
        await db.execute(
            select(func.count())
            .select_from(WorklogSyncTask)
            .outerjoin(JRIssue, JRIssue.key == WorklogSyncTask.issue_key)
            .where(*conditions)
        )
    ).scalar_one()

    items_stmt = (
        select(WorklogSyncTask, JRIssue.name.label("issue_name"))
        .select_from(WorklogSyncTask)
        .outerjoin(JRIssue, JRIssue.key == WorklogSyncTask.issue_key)
        .where(*conditions)
        .order_by(WorklogSyncTask.started_at.desc())
        .limit(limit)
        .offset(offset)
    )
    items_rows = (await db.execute(items_stmt)).all()
    items = [
        WorklogSyncTaskItem(
            id=t.id,
            status=t.status.value,
            source_id=t.source_id,
            target_id=t.target_id,
            worker_key=t.worker_key,
            issue_key=t.issue_key,
            issue_id=t.issue_id,
            content=t.content,
            started_at=t.started_at,
            time_spent=t.time_spent,
            issue_name=issue_name,
        )
        for t, issue_name in items_rows
    ]
    return WorklogSyncTasksResponse(
        summary=cast(dict, summary), total=int(total), items=items
    )


@router.get("/jr-worklogs", response_model=JRWorklogsResponse)
async def list_jr_worklogs(
    start: date | None = Query(default=None),
    end: date | None = Query(default=None),
    linked: Literal["all", "linked", "unlinked"] = Query(default="all"),
    q: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JRWorklogsResponse:
    """Реальні Tempo-worklog-и з локальної БД (`jr_worklogs`) за період.

    Scoped по `worker_key` із JWT (як `/tc-entries`/`/calendar`). Похідне
    `is_linked` (чи є наш WST-місток на цей worklog) і `issue_name` (резолв через
    `jr_issues`); фільтр `linked`, пошук `q` за назвою задачі, серверна пагінація.
    """
    if start is None or end is None:
        d_start, d_end = _current_month()
        start = start or d_start
        end = end or d_end
    _period_or_400(start, end)  # лише валідація (400, якщо start > end)

    rows, total = await JRWorklogDAO.list_with_link_state(
        db,
        worker_key=current.worker_key,
        date_from=start,
        date_to=end,
        linked=linked,
        q=q,
        limit=limit,
        offset=offset,
    )
    items = [
        JRWorklogItem(
            id=r["id"],
            description=r["description"],
            started_at=r["started_at"],
            duration=r["duration"],
            jr_issues_id=r["jr_issues_id"],
            issue_key=r["issue_key"],
            issue_name=r["issue_name"],
            is_linked=bool(r["is_linked"]),
        )
        for r in rows
    ]
    return JRWorklogsResponse(items=items, total=total)


@router.get("/jr-worklogs/duplicates", response_model=WorklogDuplicatesResponse)
async def list_jr_worklog_duplicates(
    start: date | None = Query(default=None),
    end: date | None = Query(default=None),
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WorklogDuplicatesResponse:
    """Групи дубльованих Tempo-worklog-ів поточного `worker_key` за період.

    Дубль — ≥2 рядки `jr_worklogs` із однаковим ключем дедупу
    `(jr_issues_id, jr_worker_key, started_at, duration)`, тим самим, що в
    `JRWorklogDAO.find_match`. Scoped по `worker_key` (без нього — порожньо);
    період за `started_at` (дефолт — поточний місяць), `start <= end` інакше 400.
    """
    if start is None or end is None:
        d_start, d_end = _current_month()
        start = start or d_start
        end = end or d_end
    _period_or_400(start, end)  # лише валідація (400, якщо start > end)

    groups = await JRWorklogDAO.find_duplicate_groups(
        db, worker_key=current.worker_key, date_from=start, date_to=end
    )
    return WorklogDuplicatesResponse(
        groups=[
            WorklogDuplicateGroup(
                jr_issues_id=g["jr_issues_id"],
                started_at=g["started_at"],
                duration=g["duration"],
                issue_key=g["issue_key"],
                issue_name=g["issue_name"],
                count=g["count"],
                members=[
                    WorklogDuplicateMember(
                        id=m["id"],
                        description=m["description"],
                        created_at=m["created_at"],
                        is_linked=m["is_linked"],
                    )
                    for m in g["members"]
                ],
            )
            for g in groups
        ]
    )


@router.post("/jr-worklogs/dedup", response_model=WorklogDedupResponse)
async def dedup_jr_worklogs(
    body: WorklogDedupRequest = Body(...),
    current: CurrentUser = Depends(get_current_user),
) -> WorklogDedupResponse:
    """Масово прибрати зайві worklog-и обраних груп (реальне видалення з Tempo).

    Лишає один канонічний на групу (явний `WST.target_id`, інакше min `id`),
    решту видаляє з Tempo і з дзеркала, перелінковує WST. Без `worker_key` — `400`
    (видалення персональне). Обгорнуто в `run_job` (`worklog.dedup-cleanup`), тож
    осідає в `api_jobs` як аудит. Помилка одного worklog-а — в `errors`, не валить
    усю дію.
    """
    if not current.worker_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=_MISSING_WORKER_KEY
        )

    groups = [g.worklog_ids for g in body.groups]
    async with run_job(
        trigger_name="worklog.dedup-cleanup",
        payload={"groups": groups},
        created_by=current.username,
    ) as ctx:
        ctx.result = await WorklogDedupTask().run(groups, worker=current.worker_key)

    return WorklogDedupResponse(**ctx.result)


@router.get("/tc-entries", response_model=TCEntriesResponse)
async def list_tc_entries(
    start: date | None = Query(default=None),
    end: date | None = Query(default=None),
    synced: Literal["all", "synced", "unsynced"] = Query(default="all"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TCEntriesResponse:
    """Усі записи TimeCamp за період зі станом синку (read з локальної БД).

    На відміну від `/tc-entries/untracked`, нічого не ховає — повертає всі
    записи з похідним `is_synced` (наявність worklog у Tempo для `worker_key`),
    фільтром стану й серверною пагінацією.
    """
    if start is None or end is None:
        d_start, d_end = _current_month()
        start = start or d_start
        end = end or d_end
    _period_or_400(start, end)  # лише валідація (400, якщо start > end)

    rows, total = await TCEntriesDAO.list_with_sync_state(
        db,
        worker_key=current.worker_key,
        date_from=start,
        date_to=end,
        synced=synced,
        limit=limit,
        offset=offset,
    )

    items = []
    for r in rows:
        meta = r["meta"] if isinstance(r["meta"], dict) else {}
        # issue_key: розпарсений meta.task → інакше issue_key батьківського проекту.
        issue_key = meta.get("task") or r["project_key"]
        items.append(
            TCEntryItem(
                id=r["id"],
                description=r["description"],
                start_at=r["start_at"],
                end_at=r["end_at"],
                tc_project_id=r["tc_project_id"],
                tc_project_name=r["project_name"],
                issue_key=issue_key,
                is_synced=bool(r["is_synced"]),
            )
        )
    return TCEntriesResponse(items=items, total=total)


@router.get("/tc-entries/untracked", response_model=list[UntrackedEntry])
async def list_untracked_tc_entries(
    start: date = Query(...),
    end: date = Query(...),
    _current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[UntrackedEntry]:
    period_lo, period_hi = _period_or_400(start, end)

    stmt = (
        select(TCEntry, TCProject.name)
        .outerjoin(TCProject, TCProject.id == TCEntry.tc_project_id)
        .where(
            TCEntry.start_at >= period_lo,
            TCEntry.start_at <= period_hi,
            TCEntry.meta.is_(None),
            or_(TCEntry.tc_project_id.is_(None), TCProject.issue_key.is_(None)),
        )
        .order_by(TCEntry.start_at.desc())
    )
    rows = (await db.execute(stmt)).all()
    return [
        UntrackedEntry(
            id=e.id,
            description=e.description,
            start_at=e.start_at,
            end_at=e.end_at,
            tc_project_id=e.tc_project_id,
            tc_project_name=project_name,
        )
        for e, project_name in rows
    ]
