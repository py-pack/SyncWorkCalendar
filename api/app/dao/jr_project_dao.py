from sqlalchemy import select

from .base_dao import BaseDAO
from app.models import JRProject
from app.core import sync_sessin


class JRProjectDAO(BaseDAO):
    model = JRProject

    @classmethod
    def all_keys_sync(cls) -> list[str]:
        with sync_sessin() as sessin:
            result = sessin.execute(select(cls.model.key))
            return result.scalars().all()
