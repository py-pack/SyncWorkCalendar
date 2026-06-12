from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_current_user, get_db
from app.api.schemas.sync_status import JRProjectWithCount
from app.models import JRIssue, JRProject


router = APIRouter()


@router.get("", response_model=list[JRProjectWithCount])
async def list_jr_projects(
    _current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[JRProjectWithCount]:
    counts_subq = (
        select(JRIssue.jr_project_id, func.count().label("cnt"))
        .group_by(JRIssue.jr_project_id)
        .subquery()
    )
    stmt = (
        select(JRProject, func.coalesce(counts_subq.c.cnt, 0).label("issues_count"))
        .outerjoin(counts_subq, counts_subq.c.jr_project_id == JRProject.id)
        .order_by(JRProject.key)
    )
    rows = (await db.execute(stmt)).all()
    return [
        JRProjectWithCount(
            id=p.id,
            key=p.key,
            name=p.name,
            # The column in the model is ``is_archved`` (typo preserved per D-008).
            is_archived=p.is_archved,
            is_watched=p.is_watched,
            issues_count=int(cnt),
        )
        for p, cnt in rows
    ]
