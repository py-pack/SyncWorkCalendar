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

    # Верхня межа `limit` для select-а з пошуком (щоб не віддавати все).
    _LIMIT_CAP = 50

    @classmethod
    async def list_filtered(
        cls,
        db: AsyncSession,
        project_id: int | None = None,
        q: str | None = None,
        limit: int | None = None,
    ) -> list[JRIssue]:
        """Задачі з локальної БД для екрана Jira / select-а з пошуком.

        Опційний фільтр за проектом (`project_id`), пошук `q` (ILIKE `%q%` по
        `key` OR `name`) і `limit` (капується `_LIMIT_CAP`). За наявності `q`
        сортуємо `updated_at DESC` («останні за релевантністю»), інакше — за `key`.
        """
        stmt = select(cls.model)
        if project_id is not None:
            stmt = stmt.where(cls.model.jr_project_id == project_id)

        if q:
            pattern = f"%{q}%"
            stmt = stmt.where(
                cls.model.key.ilike(pattern) | cls.model.name.ilike(pattern)
            ).order_by(cls.model.updated_at.desc())
        else:
            stmt = stmt.order_by(cls.model.key)

        if limit is not None:
            stmt = stmt.limit(min(limit, cls._LIMIT_CAP))

        result = await db.execute(stmt)
        return list(result.scalars().all())
