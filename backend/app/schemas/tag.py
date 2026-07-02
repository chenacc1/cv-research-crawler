"""Tag Pydantic schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TagCreate(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    color: str = Field(min_length=7, max_length=7)


class TagUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=64)
    color: Optional[str] = Field(default=None, min_length=7, max_length=7)


class TagDetail(BaseModel):
    id: str
    name: str
    color: str
    paper_count: int = 0
    repo_count: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


class TagListResponse(BaseModel):
    items: list[TagDetail]
