from datetime import date, datetime, time, timedelta
from typing import Literal, cast

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_current_user, get_db
from app.api.schemas.sync_status import (
    TCEntriesResponse,
    TCEntryItem,
    UntrackedEntry,
    WorklogSyncTaskItem,
    WorklogSyncTasksResponse,
)
from app.dao import TCEntriesDAO
from app.models import StatusTaskEnum, TCEntry, TCProject, WorklogSyncTask


router = APIRouter()


def _period_or_400(start: date, end: date) -> tuple[datetime, datetime]:
    if start > end:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="start must be <= end")
    return datetime.combine(start, time.min), datetime.combine(end, time.max)


def _current_month() -> tuple[date, date]:
    """Поточний місяць [перше … останнє число] як дефолт без параметрів періоду."""
    today = date.today()
    first = today.replace(day=1)
    # «28-й + 4 дні» гарантовано потрапляє в наступний місяць → його 1-ше число.
    next_first = (first.replace(day=28) + timedelta(days=4)).replace(day=1)
    return first, next_first - timedelta(days=1)


@router.get("/worklog-sync-tasks", response_model=WorklogSyncTasksResponse)
async def list_worklog_sync_tasks(
    start: date = Query(...),
    end: date = Query(...),
    status_filter: Literal[
        "pre_create", "create", "created", "pre_update", "update", "updated", "sync"
    ]
    | None = Query(default=None, alias="status"),
    _current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WorklogSyncTasksResponse:
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

    items_stmt = select(WorklogSyncTask).where(
        WorklogSyncTask.started_at >= period_lo,
        WorklogSyncTask.started_at <= period_hi,
    )
    if status_filter is not None:
        items_stmt = items_stmt.where(WorklogSyncTask.status == StatusTaskEnum(status_filter))
    items_stmt = items_stmt.order_by(WorklogSyncTask.started_at.desc())

    items_rows = (await db.execute(items_stmt)).scalars().all()
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
        )
        for t in items_rows
    ]
    return WorklogSyncTasksResponse(summary=cast(dict, summary), items=items)


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
