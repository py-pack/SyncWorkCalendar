"""Спільні хелпери періоду для read-ендпоінтів (`/tc-entries`, `/jr-issues`).

Винесено зі `routers/sync_status.py`, щоб логіка дефолтного «поточного місяця»
й валідація меж не дублювались між роутерами (rework-jira-issues-screen, 2.2).
"""
from datetime import date, datetime, time, timedelta

from fastapi import HTTPException, status


def period_or_400(start: date, end: date) -> tuple[datetime, datetime]:
    """Межі дат → `[datetime.min, datetime.max]`; `400`, якщо `start > end`."""
    if start > end:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="start must be <= end"
        )
    return datetime.combine(start, time.min), datetime.combine(end, time.max)


def current_month() -> tuple[date, date]:
    """Поточний місяць [перше … останнє число] як дефолт без параметрів періоду."""
    today = date.today()
    first = today.replace(day=1)
    # «28-й + 4 дні» гарантовано потрапляє в наступний місяць → його 1-ше число.
    next_first = (first.replace(day=28) + timedelta(days=4)).replace(day=1)
    return first, next_first - timedelta(days=1)
