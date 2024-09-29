import re
from datetime import datetime

from sqlalchemy import Integer, String, JSON, DateTime, Date
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.event import listen

from .base import Base


class JRWorklog(Base):
    jr_issues_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    meta: Mapped[dict] = mapped_column(JSON, nullable=True)

    jr_worker_key: Mapped[str] = mapped_column(String, nullable=True, index=True)
    started_at: Mapped[datetime] = mapped_column(Date(), nullable=False)
    duration: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)


def change_to_description(target: JRWorklog, value: str | None, oldvalue: str | None, initiator):
    if value == oldvalue:
        return

    patter_sunc = re.compile(r'sync\|(?P<start_time>\d{2}:\d{2})\|(?P<end_time>\d{2}:\d{2})[\-_| ]{1,3}(?P<content>.*)')

    meta = {}
    reg_groups = patter_sunc.match(value)
    if reg_groups:
        start_time: str = reg_groups.group('start_time').strip()
        end_time: str = reg_groups.group('end_time').strip()
        if start_time and end_time:
            meta['start_time'] = start_time
            meta['end_time'] = end_time

        content: str = reg_groups.group('content').strip()
        if content:
            meta['content'] = content
    else:
        if value:
            meta['content'] = value

    target.meta = meta


listen(JRWorklog.description, 'set', change_to_description)
