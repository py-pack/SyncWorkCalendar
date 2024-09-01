from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Boolean

from .base import Base


class JRProject(Base):
    key: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    is_archved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_watched: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
