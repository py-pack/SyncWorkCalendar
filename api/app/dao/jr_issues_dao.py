from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, RowMapping

from .base_dao import BaseDAO
from app.dao import JRUsersDAO, JRProjectDAO
from app.models import JRIssue
from app.services.jira import JiraIssueDTO, JiraUserDTO, JiraProjectDTO


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
        await service.update_by_keys(db, users_dto, key_sync="key")

        projects_dto = [project_dto for project_dto in projects.values()]
        service_project = JRProjectDAO()
        await service_project.update_by_keys(db, projects_dto, key_sync="key")

        service_jira_issue = JRIssuesDAO()
        await service_jira_issue.update_by_keys(db, issues)

    @classmethod
    async def get_in_keys(
        cls, db: AsyncSession, keys: list[str] | set[str]
    ) -> list[RowMapping]:
        query = await db.execute(
            select(JRIssue.id, JRIssue.key).where(JRIssue.key.in_(keys))
        )
        return list(query.mappings().all())

    @classmethod
    async def list_filtered(
        cls, db: AsyncSession, project_id: int | None = None
    ) -> list[JRIssue]:
        """Задачі з локальної БД для екрана Jira; опційний фільтр за проектом."""
        stmt = select(cls.model)
        if project_id is not None:
            stmt = stmt.where(cls.model.jr_project_id == project_id)
        stmt = stmt.order_by(cls.model.key)
        result = await db.execute(stmt)
        return list(result.scalars().all())
