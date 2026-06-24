from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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

    @classmethod
    async def watched_keys(cls, db: AsyncSession) -> list[str]:
        """Ключі відстежуваних проектів (`is_watched = true`) — для повного витягу."""
        result = await db.execute(
            select(cls.model.key).where(cls.model.is_watched.is_(True))
        )
        return list(result.scalars().all())
