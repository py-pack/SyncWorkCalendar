from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


APIJobStatusLiteral = Literal["running", "needs_verification", "verified", "failed"]


class APIJobSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    trigger_name: str
    status: APIJobStatusLiteral
    created_by: str
    verified_by: str | None
    started_at: datetime
    finished_at: datetime | None
    verified_at: datetime | None


class APIJobDetail(APIJobSummary):
    payload: dict[str, Any] | None
    result: dict[str, Any] | None
    error: str | None


class APIJobListResponse(BaseModel):
    items: list[APIJobSummary]
    total: int
