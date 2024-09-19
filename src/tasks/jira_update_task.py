from src.config import settings
from src.services.jira import JiraService, JiraIssueDTO
from src.dao import JRProjectDAO, JRIssuesDAO


class UpdateJiraTask:
    def __init__(self):
        self.client = JiraService(settings.jira.token)

    async def update_all_projects(self):
        jira_projects = self.client.get_projects()
        service_project = JRProjectDAO()
        await service_project.sync_all(jira_projects)

    async def update_jira_issues(self, key_issues: list):
        """

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
