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


class WorklogDuplicateMember(BaseModel):
    """Член групи дублів: один реальний Tempo-worklog (`jr_worklogs`)."""

    id: int
    description: str | None
    created_at: datetime | None
    # Чи вказує на цей worklog якийсь `WST.target_id` (явний лінк-місток).
    is_linked: bool


class WorklogDuplicateGroup(BaseModel):
    """Група дубльованих worklog-ів за ключем дедупу (`find_match`)."""

    jr_issues_id: int
    started_at: datetime
    duration: int
    issue_key: str | None
    issue_name: str | None
    count: int
    members: list[WorklogDuplicateMember]


class WorklogDuplicatesResponse(BaseModel):
    """Відповідь `GET /jr-worklogs/duplicates` — групи з `count > 1`."""

    groups: list[WorklogDuplicateGroup]


class WorklogDedupGroup(BaseModel):
    """Група для чистки — перелік `id` worklog-ів (members із відповіді duplicates)."""

    worklog_ids: list[int]


class WorklogDedupRequest(BaseModel):
    """Тіло `POST /jr-worklogs/dedup` — лише обрані групи (не «всі дублі»)."""

    groups: list[WorklogDedupGroup]


class WorklogDedupError(BaseModel):
    """Помилка видалення одного worklog-а (решта чистки триває далі, D3)."""

    worklog_id: int
    reason: str


class WorklogDedupResponse(BaseModel):
    """Підсумок чистки `POST /jr-worklogs/dedup`."""

    deleted: int
    kept: int
    groups: int
    errors: list[WorklogDedupError]


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
