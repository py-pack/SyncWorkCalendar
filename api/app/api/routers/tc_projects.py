from typing import Literal

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_current_user, get_db
from app.api.schemas.tc_projects import TCProjectItem, TCProjectPatchRequest
from app.core.utils import is_issue_active
from app.dao import TCProjectDAO
from app.models import JRIssue, TCProject


router = APIRouter()


def _item(
    project: TCProject,
    issue_name: str | None,
    issue_status: str | None,
) -> TCProjectItem:
    # issue_active — лише коли задачу резолвнуто локально (name NOT NULL);
    # інакше null (проект не змаплено / ключ не знайдено в jr_issues).
    issue_active = (
        is_issue_active(issue_status) if issue_name is not None else None
    )
    return TCProjectItem(
        id=project.id,
        name=project.name,
        parent_id=project.parent_id,
        color=project.color,
        is_archived=project.is_archived,
        is_sync=project.is_sync,
        issue_key=project.issue_key,
        issue_name=issue_name,
        issue_active=issue_active,
    )


@router.get("", response_model=list[TCProjectItem])
async def list_tc_projects(
    active: Literal["active", "inactive", "all"] = Query(default="all"),
    _current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[TCProjectItem]:
    # Резолв назви/статусу змапованої задачі одним LEFT JOIN (soft-link за
    # рядком-ключем, не FK) — щоб клієнт не тягнув усі задачі (D2).
    stmt = (
        select(TCProject, JRIssue.name, JRIssue.status)
        .outerjoin(JRIssue, TCProject.issue_key == JRIssue.key)
        .order_by(TCProject.name)
    )
    if active == "active":
        stmt = stmt.where(TCProject.is_archived.is_(False))
    elif active == "inactive":
        stmt = stmt.where(TCProject.is_archived.is_(True))

    rows = (await db.execute(stmt)).all()
    return [
        _item(p, issue_name, issue_status)
        for p, issue_name, issue_status in rows
    ]


@router.patch("/{tc_project_id}", response_model=TCProjectItem)
async def patch_tc_project(
    tc_project_id: int,
    body: TCProjectPatchRequest = Body(...),
    _current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TCProjectItem:
    update_fields = body.model_dump(exclude_unset=True)
    if not update_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="body must contain at least one of: is_sync, issue_key",
        )

    project = await TCProjectDAO.find(db, tc_project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="TC project not found",
        )

    for field, value in update_fields.items():
        setattr(project, field, value)
    db.add(project)

    # Резолв назви/статусу для (можливо оновленого) issue_key — щоб відповідь
    # мала той самий повний шейп, що й list (клієнт замінює рядок цілком).
    issue_name: str | None = None
    issue_status: str | None = None
    if project.issue_key:
        row = (
            await db.execute(
                select(JRIssue.name, JRIssue.status).where(
                    JRIssue.key == project.issue_key
                )
            )
        ).first()
        if row is not None:
            issue_name, issue_status = row

    return _item(project, issue_name, issue_status)
