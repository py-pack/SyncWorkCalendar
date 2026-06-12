"""Async context manager that wraps a sync-trigger in an ``api_jobs`` lifecycle.

Each phase uses its own short-lived session so an audit row lands in the DB
even when the user-facing transaction rolls back. The pattern is:

    async with run_job(trigger_name=..., payload=..., created_by=...) as ctx:
        ctx.result = await some_task(...)   # set before normal exit

On clean exit -> ``needs_verification`` with ``ctx.result`` written to the row.
On exception -> ``failed`` with ``str(exc)`` stored in ``error``, then re-raised.
"""
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any, AsyncIterator
from uuid import UUID

from app.core.db_helper import async_session_maker
from app.dao import APIJobDAO


@dataclass
class JobContext:
    job_id: UUID
    result: dict[str, Any] | None = field(default=None)


@asynccontextmanager
async def run_job(
    *,
    trigger_name: str,
    payload: dict[str, Any] | None,
    created_by: str,
) -> AsyncIterator[JobContext]:
    async with async_session_maker() as session:
        job = await APIJobDAO.create_running(
            session,
            trigger_name=trigger_name,
            payload=payload,
            created_by=created_by,
        )
        await session.commit()
        ctx = JobContext(job_id=job.id)

    try:
        yield ctx
    except Exception as exc:
        async with async_session_maker() as session:
            await APIJobDAO.mark_failed(session, ctx.job_id, str(exc))
            await session.commit()
        raise

    async with async_session_maker() as session:
        await APIJobDAO.mark_needs_verification(session, ctx.job_id, ctx.result)
        await session.commit()
