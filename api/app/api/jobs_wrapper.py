"""Спільне ядро ``api_jobs``-аудиту навколо sync-операцій.

Кожна фаза бере власну коротку сесію, тож audit-рядок лягає в БД навіть коли
request-транзакція відкочується. Патерн для HTTP:

    async with run_job(trigger_name=..., payload=..., created_by=...) as ctx:
        ctx.result = await some_task(...)   # set before normal exit

На normal-exit → ``needs_verification`` з ``ctx.result``; на exception →
``failed`` зі ``str(exc)`` у ``error``, потім re-raise.

Ядро винесене в три функції (`create_job` / `run_existing_job` / `run_job`), щоб
його переюзовувала і черга Celery поза HTTP (capability `async-task-queue`):
enqueue-тригер створює ``running``-рядок (`create_job`) і повертає `job_id`, а
воркер виконує роботу й закриває той самий рядок (`run_existing_job`). Сесії
беруться з ``db_helper`` **динамічно** (а не імпортом за іменем), бо Celery-місток
тимчасово підмінює `async_session_maker` свіжим engine під час виконання таски.
"""

from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Awaitable, Callable
from uuid import UUID

from app.core import db_helper
from app.dao import APIJobDAO


@dataclass
class JobContext:
    job_id: UUID
    result: dict[str, Any] | None = field(default=None)


async def create_job(
    *,
    trigger_name: str,
    payload: dict[str, Any] | None,
    created_by: str,
) -> UUID:
    """Створити ``api_jobs``-рядок у статусі ``running`` і повернути його id."""
    async with db_helper.async_session_maker() as session:
        job = await APIJobDAO.create_running(
            session,
            trigger_name=trigger_name,
            payload=payload,
            created_by=created_by,
        )
        await session.commit()
        return job.id


async def run_existing_job(
    job_id: UUID,
    work: Callable[[], Awaitable[dict[str, Any] | None]],
) -> dict[str, Any] | None:
    """Виконати ``work`` і закрити вже створений ``api_jobs``-рядок за наслідком.

    На normal-exit → ``needs_verification`` з результатом; на exception →
    ``failed`` (потім re-raise). Використовується чергою: enqueue-тригер уже
    створив ``running``-рядок (`create_job`), а воркер тут його завершує.
    """
    try:
        result = await work()
    except Exception as exc:
        async with db_helper.async_session_maker() as session:
            await APIJobDAO.mark_failed(session, job_id, str(exc))
            await session.commit()
        raise

    async with db_helper.async_session_maker() as session:
        await APIJobDAO.mark_needs_verification(session, job_id, result)
        await session.commit()
    return result


@asynccontextmanager
async def run_job(
    *,
    trigger_name: str,
    payload: dict[str, Any] | None,
    created_by: str,
) -> AsyncIterator[JobContext]:
    job_id = await create_job(
        trigger_name=trigger_name, payload=payload, created_by=created_by
    )
    ctx = JobContext(job_id=job_id)

    try:
        yield ctx
    except Exception as exc:
        async with db_helper.async_session_maker() as session:
            await APIJobDAO.mark_failed(session, ctx.job_id, str(exc))
            await session.commit()
        raise

    async with db_helper.async_session_maker() as session:
        await APIJobDAO.mark_needs_verification(
            session, ctx.job_id, ctx.result
        )
        await session.commit()
