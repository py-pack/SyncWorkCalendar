from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


_ISSUE_KEY_PATTERN = r"^[A-Z]{2,8}-\d{1,4}$"


class TCProjectItem(BaseModel):
    """Проект TimeCamp у відповіді `GET /tc-projects` (read, дерево + маппінг).

    Плаский елемент із полями для побудови дерева на клієнті (`parent_id`),
    кольору (`color`) і резолву змапованої Jira-задачі (`issue_name`/
    `issue_active` через LEFT JOIN `jr_issues`). Без period-залежного
    `entries_count` (D1). Цей самий шейп повертає й PATCH.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    parent_id: int | None
    color: str | None
    is_archived: bool
    is_sync: bool
    issue_key: str | None
    # Резолв через LEFT JOIN jr_issues ON tc_projects.issue_key = jr_issues.key;
    # null — проект не змаплено або ключ відсутній у локальних jr_issues.
    issue_name: str | None
    issue_active: bool | None


class TCProjectPatchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    is_sync: bool | None = None
    issue_key: Annotated[str, Field(pattern=_ISSUE_KEY_PATTERN)] | None = None
