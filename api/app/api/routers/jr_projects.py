from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_current_user, get_db
from app.api.schemas.jr_projects import (
    JRProjectPatchRequest,
    JRProjectResponse,
)
from app.api.schemas.sync_status import JRProjectWithCount
from app.dao import JRProjectDAO
from app.models import JRIssue, JRProject


router = APIRouter()


def _to_response(project: JRProject) -> JRProjectResponse:
    # Колонка моделі — ``is_archved`` (одрук збережено, D-008).
    return JRProjectResponse(
        id=project.id,
        key=project.key,
        name=project.name,
        is_archived=project.is_archved,
        is_watched=project.is_watched,
    )


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
        select(
            JRProject,
            func.coalesce(counts_subq.c.cnt, 0).label("issues_count"),
        )
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


@router.patch("/{jr_project_id}", response_model=JRProjectResponse)
async def patch_jr_project(
    jr_project_id: int,
    body: JRProjectPatchRequest = Body(...),
    _current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JRProjectResponse:
    update_fields = body.model_dump(exclude_unset=True)
    if not update_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="body must contain at least one of: is_watched",
        )

    project = await JRProjectDAO.find(db, jr_project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="JR project not found",
        )

    for field, value in update_fields.items():
        setattr(project, field, value)
    db.add(project)
    return _to_response(project)
