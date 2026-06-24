from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_current_user, get_db
from app.api.period import current_month, period_or_400
from app.api.schemas.jr_issues import JRIssueItem, JRIssuesPage
from app.dao import JRIssuesDAO


router = APIRouter()


@router.get("", response_model=JRIssuesPage)
async def list_jr_issues(
    updated_from: date | None = Query(
        default=None, description="Період активності за `updated_at` (від); дефолт — поточний місяць"
    ),
    updated_to: date | None = Query(
        default=None, description="Період активності за `updated_at` (до); дефолт — поточний місяць"
    ),
    project_id: int | None = Query(
        default=None, description="Фільтр за `jr_projects.id`"
    ),
    status: str | None = Query(
        default=None, description="Точний фільтр за `status` задачі"
    ),
    q: str | None = Query(
        default=None, description="Пошук (ILIKE) по `key` або `name`"
    ),
    limit: int = Query(default=50, ge=1, le=200, description="Максимум елементів"),
    offset: int = Query(default=0, ge=0, description="Зміщення пагінації"),
    _current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JRIssuesPage:
    """Задачі Jira за період **активності** (`updated_at`) з локальної БД, сторінковано.

    Період фільтрує задачі, з якими працювали (оновлювали) у вікні — незалежно від
    дати створення. Дефолт — поточний місяць (як `/tc-entries`); фільтри проект /
    статус / пошук; сорт `updated_at` спадно. `total` — без `limit`/`offset`.
    """
    if updated_from is None or updated_to is None:
        d_from, d_to = current_month()
        updated_from = updated_from or d_from
        updated_to = updated_to or d_to
    period_lo, period_hi = period_or_400(updated_from, updated_to)

    items, total = await JRIssuesDAO.list_paginated(
        db,
        updated_from=period_lo,
        updated_to=period_hi,
        project_id=project_id,
        status=status,
        q=q,
        limit=limit,
        offset=offset,
    )
    return JRIssuesPage(items=[JRIssueItem.model_validate(i) for i in items], total=total)


@router.get("/statuses", response_model=list[str])
async def list_jr_issue_statuses(
    _current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[str]:
    """Перелік усіх наявних у БД статусів задач (distinct) для випадайки фільтра."""
    return await JRIssuesDAO.distinct_statuses(db)
