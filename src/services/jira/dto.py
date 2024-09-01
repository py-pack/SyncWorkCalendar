from pydantic import BaseModel, field_validator


class JiraProjectDTO(BaseModel):
    id: int = None
    key: str = ''
    name: str = ''
    is_archved: bool = True

    @field_validator('id', mode='before')
    def validate_id(cls, value):
        return int(value) if value is not None and int(value) > 0 else None

    class Config:
        from_attributes = True
