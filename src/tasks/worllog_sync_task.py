from datetime import datetime

from sqlalchemy import update

from src.core import get_async_asession
from src.dao import TCProjectDAO, TCEntriesDAO, WorklogSyncTaskDAO, JRIssuesDAO
from src.models import TCProject, TCEntry, WorklogSyncTask

from .jira_update_task import UpdateJiraTask


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

    @classmethod
    async def before_create(cls, start_date: datetime, end_date: datetime):

        async with get_async_asession() as db:
            all_keys_task = await WorklogSyncTaskDAO.get_keys_period(db, start_date, end_date)
            keys_jr = await JRIssuesDAO.get_in_keys(db, all_keys_task)

            keys_except = all_keys_task - set(jr.key for jr in keys_jr)

            if keys_except:
                jira_service = UpdateJiraTask()
                await jira_service.update_jira_issues(keys_except)

            jira_id_keys = await JRIssuesDAO.get_in_keys(db, all_keys_task)

            for jira in jira_id_keys:
                await db.execute(
                    update(WorklogSyncTask).where(
                        WorklogSyncTask.issue_key == jira.key
                    ).values(issue_id=jira.id)
                )
                await db.commit()
