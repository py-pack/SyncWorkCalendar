from datetime import datetime

from sqlalchemy import update

from src.core import get_async_asession
from src.dao import TCProjectDAO, TCEntriesDAO, WorklogSyncTaskDAO, JRIssuesDAO
from src.models import TCProject, TCEntry, WorklogSyncTask, StatusTaskEnum
from src.services.jira import JiraService

from src.config import settings

from src.tasks.jira_update_task import UpdateJiraTask


class WorllogSyncTask:
    def __init__(self):
        self.jira_client = JiraService(settings.jira.token)

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
            all_tasks: list[WorklogSyncTask] = await WorklogSyncTaskDAO.get_by_period_and_status(
                db,
                start_date,
                end_date,
                status=StatusTaskEnum.pre_create
            )
            all_keys_task = set(task.issue_key for task in all_tasks)
            keys_jr = await JRIssuesDAO.get_in_keys(db, all_keys_task)

            keys_except = all_keys_task - set(jr.key for jr in keys_jr)

            if keys_except:
                jira_service = UpdateJiraTask()
                await jira_service.update_jira_issues(keys_except)

            jira_id_keys = await JRIssuesDAO.get_in_keys(db, all_keys_task)
            jira_key_dict = {jirad.key: jirad.id for jirad in jira_id_keys}

            for task in all_tasks:
                task.issue_id = jira_key_dict.get(task.issue_key)
                task.status = StatusTaskEnum.create
                await db.commit()

    async def create_worklogs(self, start_date: datetime, end_date: datetime):
        async with get_async_asession() as db:
            all_tasks: list[WorklogSyncTask] = await WorklogSyncTaskDAO.get_by_period_and_status(
                db,
                start_date,
                end_date,
                status=StatusTaskEnum.create
            )

            for wlst in all_tasks:
                result = self.jira_client.create_worklog(
                    settings.current_user,
                    int(wlst.issue_id),
                    wlst.content,
                    wlst.started_at,
                    wlst.time_spent
                )

                wlst.target_id = result.get('originId')
                wlst.status = StatusTaskEnum.created
                await db.commit()
