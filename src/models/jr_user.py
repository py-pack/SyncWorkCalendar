from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base


class JRUser(Base):
    key: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=True)
    full_name: Mapped[str] = mapped_column(String, nullable=True)
    email: Mapped[str] = mapped_column(String, nullable=True)
