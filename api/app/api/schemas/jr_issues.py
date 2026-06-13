from pydantic import BaseModel, ConfigDict


class JRIssueItem(BaseModel):
    """Задача Jira у відповіді `GET /jr-issues` (read-only, з локальної БД)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    key: str
    name: str
    jr_project_id: int
    type: str
    priority: str
    status: str
    epic_key: str | None
    parent_key: str | None
    # секунди: timeoriginalestimate / progress / aggregatetimeestimate
    estimate_plan: int
    estimate_fact: int
    estimate_rest: int
