from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_current_user, get_db
from app.api.schemas.calendar import (
    CalendarBlock,
    CalendarProject,
    CalendarResponse,
)
from app.dao import TCEntriesDAO
from app.models import StatusTaskEnum


router = APIRouter()


def _default_week() -> tuple[date, date]:
    """Поточний ISO-тиждень (Пн–Нд) як дефолт без параметрів періоду."""
    today = datetime.now(timezone.utc).date()
    monday = today - timedelta(days=today.weekday())
    return monday, monday + timedelta(days=6)


def _derive_status(wst_status: StatusTaskEnum | None) -> str:
    """Проекція `StatusTaskEnum` → стан блоку UI (D2).

    Немає WST або `pre_create` → `service`; `created`/`updated` (є `target_id`
    у Tempo) → `synced`; решта (`create` тощо) → `tempo`. `failed` тут не
    повертається — такого статусу у `StatusTaskEnum` немає (D-015).
    """
    if wst_status in (None, StatusTaskEnum.pre_create):
        return "service"
    if wst_status in (StatusTaskEnum.created, StatusTaskEnum.updated):
        return "synced"
    return "tempo"


@router.get("", response_model=CalendarResponse)
async def get_calendar(
    start: date | None = Query(default=None),
    end: date | None = Query(default=None),
    _current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CalendarResponse:
    """Тиждень блоків робочого часу поточного `worker_key` (read-only)."""
    if start is None or end is None:
        d_start, d_end = _default_week()
        start = start or d_start
        end = end or d_end
    if start > end:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start must be <= end",
        )

    rows = await TCEntriesDAO.get_calendar_blocks(
        db, worker_key=_current.worker_key, date_from=start, date_to=end
    )

    blocks: list[CalendarBlock] = []
    for r in rows:
        meta = r["meta"] if isinstance(r["meta"], dict) else {}
        # issue_key: WST (канонічний) → meta.task розпарсений → issue_key проекту.
        issue_key = r["wst_issue_key"] or meta.get("task") or r["project_key"]
        blocks.append(
            CalendarBlock(
                id=r["id"],
                start=r["start_at"],
                end=r["end_at"],
                issue_key=issue_key,
                description=r["description"],
                status=_derive_status(r["wst_status"]),
                project=CalendarProject(
                    key=r["project_key"],
                    name=r["project_name"],
                    color=r["project_color"],
                ),
            )
        )

    return CalendarResponse(blocks=blocks)
