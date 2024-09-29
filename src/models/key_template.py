from .base import Base

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column


class KeyTemplate(Base):
    template: Mapped[str] = mapped_column(String, nullable=False)
    issue_key: Mapped[str] = mapped_column(String, nullable=False)
