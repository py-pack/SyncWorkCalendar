import enum
from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator


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

    @field_validator("status", mode="before")
    @classmethod
    def _status_to_value(cls, v: Any) -> Any:
        # ORM віддає член enum `APIJobStatusEnum`; зводимо до рядкового значення,
        # бо `Literal[str]` не коерсить enum-member із `model_validate(<ORM>)`
        # (інакше — ValidationError на кожному рядку → 500). Успадковує APIJobDetail.
        return v.value if isinstance(v, enum.Enum) else v


class APIJobDetail(APIJobSummary):
    payload: dict[str, Any] | None
    result: dict[str, Any] | None
    error: str | None


class APIJobListResponse(BaseModel):
    items: list[APIJobSummary]
    total: int
