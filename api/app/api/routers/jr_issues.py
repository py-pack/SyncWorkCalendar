from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_current_user, get_db
from app.api.schemas.jr_issues import JRIssueItem
from app.dao import JRIssuesDAO


router = APIRouter()


@router.get("", response_model=list[JRIssueItem])
async def list_jr_issues(
    project_id: int | None = Query(
        default=None, description="Фільтр за `jr_projects.id`"
    ),
    q: str | None = Query(
        default=None, description="Пошук (ILIKE) по `key` або `name`"
    ),
    limit: int | None = Query(
        default=10, ge=1, description="Максимум елементів (капується ≤50)"
    ),
    _current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[JRIssueItem]:
    issues = await JRIssuesDAO.list_filtered(
        db, project_id=project_id, q=q, limit=limit
    )
    return [JRIssueItem.model_validate(i) for i in issues]
