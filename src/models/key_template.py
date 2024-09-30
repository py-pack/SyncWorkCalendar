from .base import Base

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column


class KeyTemplate(Base):
    issue_key: Mapped[str] = mapped_column(String, nullable=False)
    template: Mapped[str] = mapped_column(String, nullable=False)
