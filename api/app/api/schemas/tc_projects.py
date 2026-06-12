from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


_ISSUE_KEY_PATTERN = r"^[A-Z]{2,8}-\d{1,4}$"


class TCProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    is_sync: bool
    issue_key: str | None
    is_archived: bool


class TCProjectWithCount(TCProjectResponse):
    entries_count: int


class TCProjectPatchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    is_sync: bool | None = None
    issue_key: Annotated[str, Field(pattern=_ISSUE_KEY_PATTERN)] | None = None
