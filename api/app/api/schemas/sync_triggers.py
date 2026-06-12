from datetime import date
from typing import Any

from pydantic import BaseModel, Field, model_validator


class PeriodBody(BaseModel):
    start: date
    end: date

    @model_validator(mode="after")
    def _check_order(self) -> "PeriodBody":
        if self.start > self.end:
            raise ValueError("start must be <= end")
        return self


class IssuesKeysBody(BaseModel):
    keys: list[str] = Field(min_length=1)


class SyncTriggerResponse(BaseModel):
    job_id: str
    status: str
    result: dict[str, Any] | None = None
