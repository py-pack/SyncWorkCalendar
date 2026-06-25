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


class APIJobStatusSummary(BaseModel):
    # Лічильники по кожному статусу за фільтром періоду+тригера (ігнорує
    # фільтр статусу) — повна картина вибірки для зведення в тулбарі.
    running: int = 0
    needs_verification: int = 0
    verified: int = 0
    failed: int = 0


class APIJobListResponse(BaseModel):
    items: list[APIJobSummary]
    total: int
    summary: APIJobStatusSummary


class VerifyAllResponse(BaseModel):
    # Кількість job-ів, переведених `needs_verification`→`verified` масово.
    verified: int
