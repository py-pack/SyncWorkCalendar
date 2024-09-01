from src.dao.base_dao import BaseDAO
from src.models import TCProject


class TCProjectDAO(BaseDAO):
    model = TCProject

    @classmethod
    async def sync_all(cls, tc_projects):
        all_db_tc_project = await TCProjectDAO.all()
        await cls._sync(tc_projects, all_db_tc_project)
