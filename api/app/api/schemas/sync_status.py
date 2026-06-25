from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


_StatusTaskLiteral = Literal[
    "pre_create",
    "create",
    "created",
    "pre_update",
    "update",
    "updated",
    "sync",
]


class JRProjectWithCount(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    key: str
    name: str
    is_archived: bool
    is_watched: bool
    issues_count: int


class WorklogSyncTaskItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: _StatusTaskLiteral
    source_id: int
    target_id: int | None
    worker_key: str
    issue_key: str
    issue_id: int | None
    content: str | None
    started_at: datetime
    time_spent: int
    # Назва задачі (резолв через `jr_issues` за `issue_key`); `null`, якщо задача
    # локально невідома.
    issue_name: str | None = None


class WorklogSyncTasksResponse(BaseModel):
    summary: dict[_StatusTaskLiteral, int]
    # `summary` — по всьому періоду; `total` — кількість після фільтрів сторінки.
    total: int
    items: list[WorklogSyncTaskItem]


class JRWorklogItem(BaseModel):
    """Рядок списку `GET /jr-worklogs`: реальний Tempo-worklog зі станом звʼязку."""

    id: int
    description: str | None
    started_at: datetime
    duration: int
    jr_issues_id: int
    # Ключ і назва задачі (резолв через `jr_issues`); `null`, якщо невідома.
    issue_key: str | None
    issue_name: str | None
    # Чи звʼязаний worklog із нашим WST-містком (EXISTS на `target_id`).
    is_linked: bool


class JRWorklogsResponse(BaseModel):
    """Сторінкована відповідь `GET /jr-worklogs` (дзеркало `TCEntriesResponse`)."""

    items: list[JRWorklogItem]
    total: int


class UntrackedEntry(BaseModel):
    id: int
    description: str | None
    start_at: datetime
    end_at: datetime
    tc_project_id: int | None
    tc_project_name: str | None


class TCEntryItem(BaseModel):
    """Рядок списку `GET /tc-entries`: запис TimeCamp із похідним станом синку."""

    id: int
    description: str | None
    start_at: datetime
    end_at: datetime
    tc_project_id: int | None
    tc_project_name: str | None
    issue_key: str | None
    is_synced: bool


class TCEntriesResponse(BaseModel):
    """Сторінкована відповідь `GET /tc-entries` (прецедент `GET /api-jobs`)."""

    items: list[TCEntryItem]
    total: int
