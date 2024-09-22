from datetime import datetime
from src.config import settings
from src.services.jira import JiraService, JiraIssueDTO
from src.dao import JRProjectDAO, JRIssuesDAO, JRWorklogDAO


class UpdateJiraTask:
    def __init__(self):
        self.client = JiraService(settings.jira.token)

    async def update_all_projects(self):
        jira_projects = self.client.get_projects()
        service_project = JRProjectDAO()
        await service_project.sync_all(jira_projects)

    async def update_jira_issues(self, key_issues: list):
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
        jira_request: list[JiraIssueDTO] = self.client.search_issues(key_issues)

        service_jira_issue = JRIssuesDAO()
        await service_jira_issue.sync_by_key(jira_request)

    async def update_worklog(self, start_time: datetime, end_time: datetime):
        """
        Обновить все события

        :param start_time: - начало периода, пример:
            datetime = datetime(2024, 7, 1)
        :param end_time: - конец период, пример:
            end_time: datetime = datetime(2024, 8, 31)
        """
        service = JiraService(settings.jira.token)
        worklogs = service.serch_worklogs_by_user(start_time, end_time, settings.current_user)

        dao = JRWorklogDAO()
        await dao.sync_all_between(worklogs, start_time, end_time)

        jira_updates_keys = list(set(worklog.jr_issues_key for worklog in worklogs))
        await self.update_jira_issues(jira_updates_keys)
