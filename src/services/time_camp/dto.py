from pydantic import BaseModel, field_validator, validator
from typing import Optional
from datetime import datetime


class TCProjectDTO(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    parent_id: Optional[int] = None
    user_id: Optional[int] = None
    level: Optional[int] = None
    is_archived: bool = False
    color: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @field_validator('id', 'parent_id', 'user_id', mode='before')
    def validate_id(cls, value):
        return int(value) if value is not None and int(value) > 0 else None

    class Config:
        from_attributes = True


class TCTaskDTO(BaseModel):
    id: Optional[int] = None
    tc_project_id: Optional[int] = None
    description: Optional[str] = None
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    modify_at: Optional[datetime] = None

    @field_validator('id', 'tc_project_id', mode='before')
    def validate_id(cls, value):
        return int(value) if value is not None and int(value) > 0 else None

    class Config:
        from_attributes = True
