from datetime import date, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_current_user, get_db
from app.api.schemas.api_jobs import (
    APIJobDetail,
    APIJobListResponse,
    APIJobStatusLiteral,
    APIJobStatusSummary,
    APIJobSummary,
    VerifyAllResponse,
)
from app.dao import APIJobDAO
from app.models import APIJobStatusEnum


router = APIRouter()


def _to_dt(d: date | None) -> datetime | None:
    return datetime.combine(d, datetime.min.time()) if d is not None else None


@router.get("", response_model=APIJobListResponse)
async def list_api_jobs(
    status_filter: APIJobStatusLiteral | None = Query(default=None, alias="status"),
    trigger_name: str | None = Query(default=None),
    start: date | None = Query(default=None),
    end: date | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    _current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIJobListResponse:
    status_enum = APIJobStatusEnum(status_filter) if status_filter else None
    items, total = await APIJobDAO.list_filtered(
        db,
        status=status_enum,
        trigger_name=trigger_name,
        start=_to_dt(start),
        end=_to_dt(end),
        limit=limit,
        offset=offset,
    )
    # `summary` — за фільтром періоду+тригера, БЕЗ статус-фільтра (повна картина).
    summary = await APIJobDAO.status_summary(
        db,
        trigger_name=trigger_name,
        start=_to_dt(start),
        end=_to_dt(end),
    )
    return APIJobListResponse(
        items=[APIJobSummary.model_validate(it) for it in items],
        total=total,
        summary=APIJobStatusSummary(**summary),
    )


@router.post("/verify-all", response_model=VerifyAllResponse)
async def verify_all_api_jobs(
    trigger_name: str | None = Query(default=None),
    start: date | None = Query(default=None),
    end: date | None = Query(default=None),
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> VerifyAllResponse:
    """Масово підтвердити всі `needs_verification` за поточними фільтрами.

    Дзеркалить фільтри `GET /api-jobs` (період за `started_at` + `trigger_name`);
    `status` завжди `needs_verification`. Один атомарний `UPDATE`,
    `verified_by` = поточний користувач.
    """
    verified = await APIJobDAO.verify_matching(
        db,
        trigger_name=trigger_name,
        start=_to_dt(start),
        end=_to_dt(end),
        verified_by=current.username,
    )
    return VerifyAllResponse(verified=verified)


@router.get("/{job_id}", response_model=APIJobDetail)
async def get_api_job(
    job_id: UUID,
    _current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIJobDetail:
    job = await APIJobDAO.get_by_id(db, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="api job not found")
    return APIJobDetail.model_validate(job)


@router.post("/{job_id}/verify", response_model=APIJobDetail)
async def verify_api_job(
    job_id: UUID,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIJobDetail:
    job, error = await APIJobDAO.mark_verified(db, job_id, verified_by=current.username)
    if error == "not_found":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="api job not found")
    if error == "already_terminal":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"job is already in terminal status: {job.status.value}",
        )
    if error == "not_finished":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="job has not finished yet",
        )
    return APIJobDetail.model_validate(job)
