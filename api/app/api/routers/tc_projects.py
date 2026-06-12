from datetime import date, datetime, time, timezone
from calendar import monthrange

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_current_user, get_db
from app.api.schemas.tc_projects import (
    TCProjectPatchRequest,
    TCProjectResponse,
    TCProjectWithCount,
)
from app.dao import TCProjectDAO
from app.models import TCEntry, TCProject


router = APIRouter()


def _default_period() -> tuple[date, date]:
    today = datetime.now(timezone.utc).date()
    last_day = monthrange(today.year, today.month)[1]
    return today.replace(day=1), today.replace(day=last_day)


@router.get("", response_model=list[TCProjectWithCount])
async def list_tc_projects(
    start: date | None = Query(default=None),
    end: date | None = Query(default=None),
    _current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[TCProjectWithCount]:
    if start is None or end is None:
        start_default, end_default = _default_period()
        start = start or start_default
        end = end or end_default
    if start > end:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="start must be <= end")

    period_lo = datetime.combine(start, time.min)
    period_hi = datetime.combine(end, time.max)

    counts_subq = (
        select(TCEntry.tc_project_id, func.count().label("cnt"))
        .where(TCEntry.start_at >= period_lo, TCEntry.start_at <= period_hi)
        .group_by(TCEntry.tc_project_id)
        .subquery()
    )

    stmt = (
        select(TCProject, func.coalesce(counts_subq.c.cnt, 0).label("entries_count"))
        .outerjoin(counts_subq, counts_subq.c.tc_project_id == TCProject.id)
        .order_by(TCProject.name)
    )
    rows = (await db.execute(stmt)).all()
    return [
        TCProjectWithCount(
            id=p.id,
            name=p.name,
            is_sync=p.is_sync,
            issue_key=p.issue_key,
            is_archived=p.is_archived,
            entries_count=int(cnt),
        )
        for p, cnt in rows
    ]


@router.patch("/{tc_project_id}", response_model=TCProjectResponse)
async def patch_tc_project(
    tc_project_id: int,
    body: TCProjectPatchRequest = Body(...),
    _current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TCProjectResponse:
    update_fields = body.model_dump(exclude_unset=True)
    if not update_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="body must contain at least one of: is_sync, issue_key",
        )

    project = await TCProjectDAO.find(db, tc_project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="TC project not found")

    for field, value in update_fields.items():
        setattr(project, field, value)
    db.add(project)
    return TCProjectResponse.model_validate(project)
