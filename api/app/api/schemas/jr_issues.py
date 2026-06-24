from pydantic import BaseModel, ConfigDict, computed_field

from app.core.utils import is_issue_active


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

    @computed_field  # type: ignore[prop-decorator]
    @property
    def active(self) -> bool:
        """`True`, якщо `status` не в «done»-сеті (похідне, для тьмяності в UI)."""
        return is_issue_active(self.status)


class JRIssuesPage(BaseModel):
    """Сторінкована відповідь `GET /jr-issues` (прецедент `TCEntriesResponse`)."""

    items: list[JRIssueItem]
    total: int
