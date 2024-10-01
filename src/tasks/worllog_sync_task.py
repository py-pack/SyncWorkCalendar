from datetime import datetime

from src.core import get_async_asession
from src.dao import TCProjectDAO, TCEntriesDAO, WorklogSyncTaskDAO
from src.models import TCProject, TCEntry, WorklogSyncTask


class WorllogSyncTask:
    def __init__(self):
        pass

    @classmethod
    async def create_task_for_sync(cls, start_date: datetime, end_date: datetime):
        async with get_async_asession() as db:
            dao = TCEntriesDAO()
            worklogs_dict = await dao.get_entries_for_worklogs(db, start_date, end_date)

            dao_wst = WorklogSyncTaskDAO()
            for worklog in worklogs_dict:
                exist = await dao_wst.exists(db, worklog.source_id, 'source_id')
                if not exist:
                    wst = WorklogSyncTask.create(**worklog.model_dump())
                    db.add(wst)
                    await db.commit()
