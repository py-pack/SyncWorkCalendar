from datetime import datetime
from src.config import settings
from src.services.jira import JiraService, JiraIssueDTO
from src.dao import JRProjectDAO, JRIssuesDAO, JRWorklogDAO

from src.core import get_async_asession


class UpdateJiraTask:
    def __init__(self):
        self.client = JiraService(settings.jira.token)

    async def update_all_projects(self):
        async with get_async_asession() as db:
            jira_projects = self.client.get_projects()
            service_project = JRProjectDAO()
            await service_project.sync_all(db, jira_projects)

    async def update_jira_issues(self, key_issues: list | set):
        """
        Обновить все issue Jira для определенных ключей

        :param key_issues: - Keys Issue Jira
        key_issues = [
            'PEG-490',
            'PEG-527',
            'MP-86',
        ]
        :return: void
        """
        async with get_async_asession() as db:
            jira_request: list[JiraIssueDTO] = self.client.search_issues(key_issues)

            service_jira_issue = JRIssuesDAO()
            await service_jira_issue.sync_by_key(db, jira_request)

    async def update_worklog(
        self,
        start_time: datetime,
        end_time: datetime,
        worker: str | None = None,
    ):
        """
        Обновить все события

        :param start_time: - начало периода, пример:
            datetime = datetime(2024, 7, 1)
        :param end_time: - конец период, пример:
            end_time: datetime = datetime(2024, 8, 31)
        :param worker: Jira key that filters worklogs in Tempo. HTTP callers
            pass JWT.worker_key; CLI/notebook callers fall back to
            ``settings.current_user``.
        """
        actor = worker or settings.current_user
        async with get_async_asession() as db:
            service = JiraService(settings.jira.token)
            worklogs = service.serch_worklogs_by_user(start_time, end_time, actor)

            if len(worklogs) == 0:
                return

            dao = JRWorklogDAO()
            await dao.sync_all_between(db, worklogs, start_time, end_time)

            jira_updates_keys = list(set(worklog.jr_issues_key for worklog in worklogs))
            await self.update_jira_issues(jira_updates_keys)
