from datetime import date, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_current_user, get_db
from app.api.jobs_wrapper import create_job
from app.api.routers.sync_triggers import TRIGGER_WORK
from app.api.schemas.api_jobs import (
    APIJobDetail,
    APIJobListResponse,
    APIJobStatusLiteral,
    APIJobStatusSummary,
    APIJobSummary,
    VerifyAllResponse,
)
from app.core.db_helper import async_session_maker
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


@router.post("/{job_id}/retry", response_model=APIJobDetail)
async def retry_api_job(
    job_id: UUID,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIJobDetail:
    """Синхронно повторити одну `failed`-job-у її ж `trigger_name`+`payload`.

    Створює **нову** `api_jobs`-джобу (стара `failed` лишається в історії, D4) і
    прогоняє ту саму роботу через спільний реєстр `TRIGGER_WORK` (реюз `_do_*` зі
    `sync_triggers`). Повертає `APIJobDetail` **нової** job-и в **обох** випадках:
    успіх → `needs_verification`, повторне падіння → `failed`. Тобто синхронна
    невдада роботи — це `200` з новою `failed`-джобою, **не** `500` (D3).

    - `404`, якщо job-и немає.
    - `409`, якщо `status != failed` (ретраяться лише впалі).
    - `422`, якщо `trigger_name` невідомий реєстру (`trigger is not retryable`).
    """
    job = await APIJobDAO.get_by_id(db, job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="api job not found"
        )
    if job.status != APIJobStatusEnum.failed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="job is not in failed status",
        )
    work = TRIGGER_WORK.get(job.trigger_name)
    if work is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="trigger is not retryable",
        )

    # Нова `running`-джоба з тими ж параметрами; стару не мутуємо.
    payload = job.payload
    new_job_id = await create_job(
        trigger_name=job.trigger_name,
        payload=payload,
        created_by=current.username,
    )

    # Синхронне виконання з гарантованим закриттям рядка у власній сесії (як
    # `jobs_wrapper`/`_execute`): re-raise НЕ робимо — повертаємо нову job-у завжди.
    try:
        result = await work(payload)
    except Exception as exc:
        async with async_session_maker() as session:
            await APIJobDAO.mark_failed(session, new_job_id, str(exc))
            await session.commit()
    else:
        async with async_session_maker() as session:
            await APIJobDAO.mark_needs_verification(session, new_job_id, result)
            await session.commit()

    new_job = await APIJobDAO.get_by_id(db, new_job_id)
    return APIJobDetail.model_validate(new_job)
