from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase, declared_attr
from sqlalchemy.orm import Mapped, mapped_column

from src.config import settings
from src.utils import camel_case_to_snake_case


class Base(DeclarativeBase):
    __abstract__ = True

    metadata = MetaData(naming_convention=settings.db.naming_convention)

    @declared_attr.directive
    def __tablename__(cls):
        return f"{camel_case_to_snake_case(cls.__name__)}s"

    id: Mapped[int] = mapped_column(primary_key=True)
