from datetime import date, datetime, time

from pydantic import BaseModel

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import TCEntry, TCProject, StatusTaskEnum, WorklogSyncTask
from app.config import settings

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
    async def get_calendar_blocks(
        cls,
        db: AsyncSession,
        worker_key: str | None,
        date_from: date,
        date_to: date,
    ) -> list[dict]:
        """Блоки тижня для read-екрана календаря.

        `tc_entry` (відпрацьований час) ⋈ `tc_project` (колір/назва/issue_key)
        ⋈ `worklog_sync_task` (стан синку). WST приєднується **лише** для
        поточного `worker_key`, тож стан чужого worklog-а не протікає; entries
        без WST лишаються (стан `service`). Період — за `tc_entry.start_at`.

        Лише читання — без мутацій і без нових колонок (D3 у `design.md`).
        """
        stmt = (
            select(
                TCEntry.id,
                TCEntry.start_at,
                TCEntry.end_at,
                TCEntry.description,
                TCEntry.meta,
                TCProject.name.label("project_name"),
                TCProject.color.label("project_color"),
                TCProject.issue_key.label("project_key"),
                WorklogSyncTask.status.label("wst_status"),
                WorklogSyncTask.issue_key.label("wst_issue_key"),
            )
            .select_from(TCEntry)
            .outerjoin(TCProject, TCProject.id == TCEntry.tc_project_id)
            .outerjoin(
                WorklogSyncTask,
                and_(
                    WorklogSyncTask.source_id == TCEntry.id,
                    WorklogSyncTask.worker_key == worker_key,
                ),
            )
            .where(
                and_(
                    TCEntry.start_at >= datetime.combine(date_from, time.min),
                    TCEntry.start_at <= datetime.combine(date_to, time.max),
                )
            )
            .order_by(TCEntry.start_at)
        )
        return list((await db.execute(stmt)).mappings().all())

    async def get_entries_for_worklogs(
        self, db: AsyncSession,
        date_from: datetime,
        date_to: datetime
    ) -> list[WorklogTaskDTO]:
        entries_query = await db.execute(
            select(
                TCEntry.id,
                TCEntry.description,
                TCEntry.meta,
                TCEntry.start_at,
                TCEntry.end_at,
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
            else:
                issue_key = entry.issue_key

            content = self._create_content_by_template(
                entry.description,
                issue_key,
                entry.start_at,
                entry.end_at
            )
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

    def _create_content_by_template(self, content: str, key: str, start: datetime, end: datetime) -> str:
        content = content.replace(key, "").strip(" -")

        result = f"sync|{start.strftime("%H:%M")}|{end.strftime("%H:%M")}"
        if content:
            result += f" - {content}"

        return result
