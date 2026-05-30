from datetime import date, datetime, time
from typing import Literal, cast

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import CurrentUser, get_current_user, get_db
from src.api.schemas.sync_status import (
    UntrackedEntry,
    WorklogSyncTaskItem,
    WorklogSyncTasksResponse,
)
from src.models import StatusTaskEnum, TCEntry, TCProject, WorklogSyncTask


router = APIRouter()


def _period_or_400(start: date, end: date) -> tuple[datetime, datetime]:
    if start > end:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="start must be <= end")
    return datetime.combine(start, time.min), datetime.combine(end, time.max)


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
