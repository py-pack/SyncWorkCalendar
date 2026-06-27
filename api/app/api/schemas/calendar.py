from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


# Стан блоку для UI — проекція `StatusTaskEnum` (D2). `failed` бекенд не віддає:
# такого статусу у `worklog_sync_tasks` немає (це стан `api_jobs`, не WST).
CalendarStatusLiteral = Literal["service", "tempo", "synced"]


class CalendarProject(BaseModel):
    """Проект блоку — джерело кольору і назви на фронті."""

    model_config = ConfigDict(from_attributes=True)

    key: str | None = None
    name: str | None = None
    color: str | None = None


class CalendarBlock(BaseModel):
    """Один блок робочого часу.

    Read-проекція `tc_entry` (відпрацьований час) ⋈ `worklog_sync_task`
    (стан синку) ⋈ `tc_project` (колір/назва). Лише читання — без мутацій.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    start: datetime
    end: datetime
    issue_key: str | None = None
    description: str | None = None
    status: CalendarStatusLiteral
    # Окремий прапор (НЕ стан синку): worklog блоку входить у групу дублів у
    # періоді (capability `api-worklog-dedup`). Набір станів синку незмінний.
    duplicate: bool = False
    project: CalendarProject


class CalendarResponse(BaseModel):
    """Тиждень блоків для авторизованого `worker_key`."""

    blocks: list[CalendarBlock]
