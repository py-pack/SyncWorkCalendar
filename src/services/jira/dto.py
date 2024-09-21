from typing import Optional
from datetime import datetime, date
from pydantic import BaseModel, field_validator


class JiraProjectDTO(BaseModel):
    id: int = None
    key: str = ''
    name: str = ''
    is_archved: bool = False

    @field_validator('id', mode='before')
    def validate_id(cls, value):
        return int(value) if value is not None and int(value) > 0 else None

    class Config:
        from_attributes = True


class JiraUserDTO(BaseModel):
    key: str = ''
    name: Optional[str] = None
    full_name: Optional[str] = None
    email: Optional[str] = None

    class Config:
        from_attributes = True


class JiraIssueDTO(BaseModel):
    id: int = None

    key: str = None
    name: str = None
    jr_project_id: int = None
    epic_key: Optional[str] = None
    parent_key: Optional[str] = None
    type: str = None
    priority: str = None
    status: str = None

    jr_creator_key: Optional[str] = None
    jr_reporter_key: Optional[str] = None

    estimate_plan: int = 0
    estimate_fact: int = 0
    estimate_rest: int = 0

    created_at: datetime = None
    updated_at: datetime = None

    project: Optional[JiraProjectDTO] = None
    creator: Optional[JiraUserDTO] = None
    reporter: Optional[JiraUserDTO] = None

    @field_validator('id', 'jr_project_id', mode='before')
    def validate_id(cls, value):
        return int(value) if value is not None and int(value) > 0 else None

    @field_validator('estimate_plan', 'estimate_fact', 'estimate_rest', mode='before')
    def validate_estimate(cls, value):
        return int(value) if value is not None else 0

    class Config:
        from_attributes = True


class JiraWorklogDTO(BaseModel):
    id: int = None
    jr_issues_id: int = None
    jr_issues_key: Optional[str] = None
    description: str = None
    jr_worker_key: Optional[str] = None
    started_at: date = None
    duration: int = None
    created_at: datetime = None
    updated_at: datetime = None

    issue: Optional[JiraIssueDTO] = None

    @field_validator('id', 'jr_issues_id', mode='before')
    def validate_id(cls, value):
        return int(value) if value is not None and int(value) > 0 else None

    class Config:
        from_attributes = True
