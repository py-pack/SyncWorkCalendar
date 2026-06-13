from sqlalchemy import exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import APIUser

from .base_dao import BaseDAO


class APIUserDAO(BaseDAO):
    model = APIUser

    @classmethod
    async def get_by_username(
        cls, db: AsyncSession, username: str
    ) -> APIUser | None:
        result = await db.execute(
            select(cls.model).where(cls.model.username == username)
        )
        return result.scalar_one_or_none()

    @classmethod
    async def get_by_email(
        cls, db: AsyncSession, email: str
    ) -> APIUser | None:
        """Знайти активного користувача за e-mail (регістронезалежно).

        Зіставлення Google-акаунта: і збережений e-mail, і вхідний значення
        порівнюються у нижньому регістрі. Неактивні рядки не повертаються —
        Google-вхід для них має давати ту саму 401, що й невідомий e-mail.
        """
        normalized = email.strip().lower()
        result = await db.execute(
            select(cls.model).where(
                func.lower(cls.model.email) == normalized,
                cls.model.is_active.is_(True),
            )
        )
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
            select(func.count())
            .select_from(cls.model)
            .where(cls.model.is_active.is_(True))
        )
        return int(result.scalar_one())

    # --- Users CRUD (capability `api-users-management`) ---

    @classmethod
    async def list_all(cls, db: AsyncSession) -> list[APIUser]:
        """Усі користувачі, відсортовані за `username` (для екрана «Користувачі»)."""
        result = await db.execute(
            select(cls.model).order_by(cls.model.username)
        )
        return list(result.scalars().all())

    @classmethod
    async def username_exists(
        cls, db: AsyncSession, username: str, exclude_id: int | None = None
    ) -> bool:
        stmt = select(cls.model.id).where(cls.model.username == username)
        if exclude_id is not None:
            stmt = stmt.where(cls.model.id != exclude_id)
        return bool((await db.execute(select(exists(stmt)))).scalar_one())

    @classmethod
    async def email_exists(
        cls, db: AsyncSession, email: str, exclude_id: int | None = None
    ) -> bool:
        """Чи зайнятий e-mail (регістронезалежно). `exclude_id` — для PATCH."""
        normalized = email.strip().lower()
        stmt = select(cls.model.id).where(
            func.lower(cls.model.email) == normalized
        )
        if exclude_id is not None:
            stmt = stmt.where(cls.model.id != exclude_id)
        return bool((await db.execute(select(exists(stmt)))).scalar_one())

    @classmethod
    async def create(
        cls,
        db: AsyncSession,
        *,
        username: str,
        email: str | None = None,
        worker_key: str | None = None,
        password_hash: str | None = None,
    ) -> APIUser:
        """Invite-флоу: e-mail нормалізуємо у нижній регістр (як `get_by_email`).

        `password_hash=None` → вхід лише через Google. `flush`, щоб у відповіді
        був згенерований `id` (коміт робить залежність `get_db` на виході).
        """
        user = cls.model(
            username=username,
            email=email.strip().lower() if email else None,
            password_hash=password_hash,
            worker_key=worker_key,
        )
        db.add(user)
        await db.flush()
        return user

    @classmethod
    async def update(
        cls, db: AsyncSession, user: APIUser, **fields
    ) -> APIUser:
        for field, value in fields.items():
            setattr(user, field, value)
        db.add(user)
        await db.flush()
        return user

    @classmethod
    async def delete(cls, db: AsyncSession, user: APIUser) -> None:
        await db.delete(user)
        await db.flush()
