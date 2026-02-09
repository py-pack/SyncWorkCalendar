from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, RowMapping

from .base_dao import BaseDAO
from src.dao import JRUsersDAO, JRProjectDAO
from src.models import JRIssue
from src.services.jira import JiraIssueDTO, JiraUserDTO, JiraProjectDTO


class JRIssuesDAO(BaseDAO):
    model = JRIssue

    async def sync_by_key(self, db: AsyncSession, issues: List[JiraIssueDTO]):
        users: dict[str, JiraUserDTO] = {}
        projects: dict[str, JiraProjectDTO] = {}

        for issue in issues:
            if issue.creator is not None:
                if users.get(issue.creator.key) is None:
                    users[issue.creator.key] = issue.creator
            if issue.reporter is not None:
                if users.get(issue.reporter.key) is None:
                    users[issue.reporter.key] = issue.reporter
            if issue.project is not None:
                if users.get(issue.project.key) is None:
                    projects[issue.project.key] = issue.project

        users_dto = [user for user_id, user in users.items()]
        service = JRUsersDAO()
        await service.update_by_keys(db, users_dto, key_sync='key')

        projects_dto = [project_dto for project_dto in projects.values()]
        service_project = JRProjectDAO()
        await service_project.update_by_keys(db, projects_dto, key_sync='key')

        service_jira_issue = JRIssuesDAO()
        await service_jira_issue.update_by_keys(db, issues)

    @classmethod
    async def get_in_keys(cls, db: AsyncSession, keys: list[str] | set[str]) -> list[RowMapping]:
        query = await db.execute(
            select(JRIssue.id, JRIssue.key).where(JRIssue.key.in_(keys))
        )
        return list(query.mappings().all())
