from datetime import date, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_current_user, get_db
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
    """Синхронно перезапустити **ту саму** `failed`-job-у на місці (без нової джоби).

    Рестарт іде через атомарний compare-and-swap `failed → running`
    (`retry_claim`) — це й guard від подвійного кліку: другий/паралельний клік
    бачить, що рядок уже не `failed`, і отримує `409`, жодної роботи не запускає.
    Після успішного CAS прогоняє ту саму роботу через реєстр `TRIGGER_WORK` (реюз
    `_do_*` зі `sync_triggers`) і закриває **той самий** рядок: успіх →
    `needs_verification`, повторне падіння → `failed`. Повертає `APIJobDetail`
    **того самого** `id` в обох випадках; синхронна невдача роботи — це `200`, **не**
    `500` (D2/D3).

    - `404`, якщо job-и немає.
    - `409`, якщо CAS не зачепив рядок (`status != failed`: уже `running` від
      попереднього кліку, `needs_verification`/`verified`).
    - `422`, якщо `trigger_name` невідомий реєстру (рядок закривається у `failed`
      з поясненням; guard уже зайняв рядок, тож CAS лишається коректним).
    """
    job = await APIJobDAO.get_by_id(db, job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="api job not found"
        )
    # Беремо параметри роботи до CAS/коміту (expire_on_commit=False, але рядок
    # мутуємо Core-`UPDATE`-ом, тож читаємо ORM-поля наперед у локальні змінні).
    trigger_name = job.trigger_name
    payload = job.payload

    # Атомарний CAS `failed → running` — самодостатній guard від подвійного кліку.
    claimed = await APIJobDAO.retry_claim(db, job_id)
    if not claimed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="job is not in failed status",
        )
    # Зафіксувати рестарт одразу: звільняє row-lock і робить `running` видимим для
    # паралельного кліку (той одразу дістане `409`), а не лише в кінці запиту.
    await db.commit()

    work = TRIGGER_WORK.get(trigger_name)
    if work is None:
        async with async_session_maker() as session:
            await APIJobDAO.mark_failed(session, job_id, "trigger is not retryable")
            await session.commit()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="trigger is not retryable",
        )

    # Синхронне виконання з гарантованим закриттям **того самого** рядка у власній
    # сесії (як `jobs_wrapper`): re-raise НЕ робимо — повертаємо цей рядок завжди.
    try:
        result = await work(payload)
    except Exception as exc:
        async with async_session_maker() as session:
            await APIJobDAO.mark_failed(session, job_id, str(exc))
            await session.commit()
    else:
        async with async_session_maker() as session:
            await APIJobDAO.mark_needs_verification(session, job_id, result)
            await session.commit()

    # Свіжа сесія: `db` має застарілу копію рядка (expire_on_commit=False), а
    # фінальний стан закрили інші сесії.
    async with async_session_maker() as session:
        refreshed = await APIJobDAO.get_by_id(session, job_id)
        return APIJobDetail.model_validate(refreshed)
