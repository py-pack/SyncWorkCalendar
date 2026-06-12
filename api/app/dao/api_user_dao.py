from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import APIUser

from .base_dao import BaseDAO


class APIUserDAO(BaseDAO):
    model = APIUser

    @classmethod
    async def get_by_username(cls, db: AsyncSession, username: str) -> APIUser | None:
        result = await db.execute(select(cls.model).where(cls.model.username == username))
        return result.scalar_one_or_none()

    @classmethod
    async def create_user(
        cls,
        db: AsyncSession,
        username: str,
        password_hash: str,
        worker_key: str | None = None,
    ) -> APIUser:
        user = cls.model(
            username=username,
            password_hash=password_hash,
            worker_key=worker_key,
        )
        db.add(user)
        return user

    @classmethod
    async def count_active(cls, db: AsyncSession) -> int:
        result = await db.execute(
            select(func.count()).select_from(cls.model).where(cls.model.is_active.is_(True))
        )
        return int(result.scalar_one())
