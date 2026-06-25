"""Безпечний місток async-коду в синхронні Celery-таски.

``asyncpg``-зʼєднання привʼязані до event-loop, у якому створені, а prefork-пул
Celery переюзовує воркер-процеси між тасками. Тож глобальний `async_engine`,
створений в одному loop, ламається при виклику з наступного. Рішення (D3):
кожна таска проганяє роботу через свіжий event-loop (`asyncio.run`) із **свіжим**
engine/sessionmaker, тимчасово підмінює глобалі `db_helper` (щоб
`get_async_asession` і DAO підхопили їх), і дисипує engine на виході. Як
підстраховка — воркер запускається з `--max-tasks-per-child`.
"""

import asyncio
from typing import Any, Awaitable, Callable
from uuid import UUID

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.api.jobs_wrapper import create_job, run_existing_job
from app.config import settings
from app.core import db_helper


def run_async(factory: Callable[[], Awaitable[Any]]) -> Any:
    """Виконати корутину `factory()` у свіжому loop зі свіжим DB-engine.

    `factory` — фабрика корутини (викликається **всередині** loop), бо корутину
    не можна створити поза loop і переносити між ними.
    """

    async def _runner() -> Any:
        engine = create_async_engine(str(settings.db.url), poolclass=NullPool)
        maker = async_sessionmaker(
            bind=engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )
        prev_engine = db_helper.async_engine
        prev_maker = db_helper.async_session_maker
        db_helper.async_engine = engine
        db_helper.async_session_maker = maker
        try:
            return await factory()
        finally:
            db_helper.async_session_maker = prev_maker
            db_helper.async_engine = prev_engine
            await engine.dispose()

    return asyncio.run(_runner())


def run_audited_task(
    *,
    trigger_name: str,
    created_by: str,
    work: Callable[[], Awaitable[dict[str, Any] | None]],
    payload: dict[str, Any] | None = None,
    job_id: str | None = None,
) -> str:
    """Прогнати `work` під ``api_jobs``-аудитом у Celery-воркері.

    Якщо `job_id` передано (enqueue-тригер уже створив ``running``-рядок) —
    закриваємо його; інакше (beat / самостійна таска) — створюємо власний рядок.
    Повертає рядковий `job_id` (зручно як результат Celery-таски).
    """

    async def factory() -> str:
        jid = (
            UUID(job_id)
            if job_id
            else await create_job(
                trigger_name=trigger_name,
                payload=payload,
                created_by=created_by,
            )
        )
        await run_existing_job(jid, work)
        return str(jid)

    return run_async(factory)
