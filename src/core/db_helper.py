from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from src.config import settings


class DatabaseHelper:
    def __init__(
        self,
        url: str,
        echo: bool = False,  # Виводити логи DB
        echo_pool: bool = False,  # Виводити більш широкі логи
        pool_size: int = 5,  # кількість відкрити з'єднань
        max_overflow: int = 10,  # кількість підключень в пулі
    ):
        self.engine = create_async_engine(
            url=url,
            echo=echo,
            echo_pool=echo_pool,
            pool_size=pool_size,
            max_overflow=max_overflow,
        )

        self.session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )

    async def dispose(self) -> None:
        await self.engine.dispose()

    async def session_getter(self) -> AsyncGenerator[AsyncSession, None]:
        async with self.session_factory() as session:
            yield session


db_helper = DatabaseHelper(
    url=str(settings.db.url),
    echo=settings.db.echo,
    echo_pool=bool(settings.db.echo_pool),
    pool_size=int(settings.db.pool_size),
    max_overflow=settings.db.max_overflow,
)
