from pydantic import BaseModel, ConfigDict


class JRProjectResponse(BaseModel):
    """Проект Jira після `PATCH /jr-projects/{id}` (локальні прапори)."""

    id: int
    key: str
    name: str
    is_archived: bool
    is_watched: bool


class JRProjectPatchRequest(BaseModel):
    """Тіло `PATCH /jr-projects/{id}` — лише локальний прапор `is_watched`.

    У Jira нічого не пишемо (як `tc-projects` PATCH міняє лише локальні поля).
    """

    model_config = ConfigDict(extra="forbid")

    is_watched: bool | None = None
