from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import APIUser

from .base_dao import BaseDAO


class APIUserDAO(BaseDAO):
    model = APIUser

    @classmethod
    async def get_by_username(cls, db: AsyncSession, username: str) -> APIUser | None:
        result = await db.execute(select(cls.model).where(cls.model.username == username))
        return result.scalar_one_or_none()

    @classmethod
    async def count_active(cls, db: AsyncSession) -> int:
        result = await db.execute(
            select(func.count()).select_from(cls.model).where(cls.model.is_active.is_(True))
        )
        return int(result.scalar_one())
