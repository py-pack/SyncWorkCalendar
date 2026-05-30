from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field, model_validator


class PeriodQuery(BaseModel):
    """Reusable ``?start=&end=`` query holder. Validates ``start <= end``."""

    start: date | None = None
    end: date | None = None

    @model_validator(mode="after")
    def _check_order(self) -> "PeriodQuery":
        if self.start is not None and self.end is not None and self.start > self.end:
            raise ValueError("start must be <= end")
        return self


class PeriodBody(BaseModel):
    start: date
    end: date

    @model_validator(mode="after")
    def _check_order(self) -> "PeriodBody":
        if self.start > self.end:
            raise ValueError("start must be <= end")
        return self


class BackgroundQuery(BaseModel):
    background: bool = False


class ErrorResponse(BaseModel):
    detail: str


class HealthResponse(BaseModel):
    status: str = "ok"


class JobRefResponse(BaseModel):
    """Minimal sync-trigger response shape used across all /sync/** endpoints."""

    job_id: str
    status: str
    result: dict[str, Any] | None = None
