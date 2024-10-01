from datetime import datetime, time

from pydantic import BaseModel

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import TCEntry, TCProject, StatusTaskEnum, WorklogSyncTask
from src.config import settings

from .base_dao import BaseDAO


class WorklogTaskDTO(BaseModel):
    status: str = None
    source_id: int = None
    worker_key: str = None
    issue_key: str = None
    content: str = None
    started_at: datetime = None
    time_spent: int = None

    class Config:
        from_attributes = True


class TCEntriesDAO(BaseDAO):
    model = TCEntry

    @classmethod
    async def sync_all_between(cls, db: AsyncSession, entries, date_from: datetime, date_to: datetime):
        entries_db = (await db.execute(
            select(cls.model).where(
                and_(
                    cls.model.start_at >= datetime.combine(date_from.date(), time.min),
                    cls.model.start_at <= datetime.combine(date_to.date(), time.max),
                )
            ))).scalars().all()

        await cls._sync(db, entries, entries_db)

    @classmethod
    async def get_entries_for_worklogs(
        cls, db: AsyncSession,
        date_from: datetime,
        date_to: datetime
    ) -> list[WorklogTaskDTO]:
        entries_query = await db.execute(
            select(
                TCEntry.id,
                TCEntry.description,
                TCEntry.meta,
                TCEntry.start_at,
                TCEntry.duration,
                TCProject.issue_key,
            )
            .select_from(TCEntry)
            .join(TCProject, TCProject.id == TCEntry.tc_project_id)
            .outerjoin(WorklogSyncTask, WorklogSyncTask.source_id == TCEntry.id)
            .where(and_(
                TCProject.is_sync == True,
                WorklogSyncTask.source_id == None,
                TCEntry.start_at >= datetime.combine(date_from.date(), time.min),
                TCEntry.start_at <= datetime.combine(date_to.date(), time.max),
            ))
        )
        entries = entries_query.mappings().all()

        result = []
        worker_key = settings.current_user

        for entry in entries:
            if entry.meta and entry.meta.get('task'):
                issue_key = entry.meta.get('task')
                content = entry.description
            else:
                issue_key = entry.issue_key
                content = entry.description

            result.append(WorklogTaskDTO(
                status=StatusTaskEnum.pre_create,
                source_id=entry.id,
                worker_key=worker_key,
                issue_key=issue_key,
                content=content,
                started_at=entry.start_at,
                time_spent=entry.duration,
            ))

        return result
