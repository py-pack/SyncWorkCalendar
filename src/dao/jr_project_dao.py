from typing import List

from .base_dao import BaseDAO
from src.models import JRProject
from src.services.jira import JiraProjectDTO


class JRProjectDao(BaseDAO):
    model = JRProject

    @classmethod
    async def sync_all(cls, projects: List[JiraProjectDTO]):
        projects_db = await cls.all()
        await cls._sync(projects, projects_db)
