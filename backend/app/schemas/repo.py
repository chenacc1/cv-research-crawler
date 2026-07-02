"""Repository Pydantic schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.common import TagRef


class RepoSummary(BaseModel):
    id: str
    full_name: str
    description: Optional[str] = None
    url: str
    stars: int
    forks: int
    language: Optional[str] = None
    topics: list[str] = Field(default_factory=list)
    pushed_at: Optional[datetime] = None
    crawled_at: datetime
    last_crawled_at: datetime
    tags: list[TagRef] = Field(default_factory=list)
    summary_cn: Optional[str] = None
    summary_en: Optional[str] = None

    model_config = {"from_attributes": True}


class RepoDetail(RepoSummary):
    """In V1, RepoDetail is identical to RepoSummary."""
    pass


class RepoTagUpdate(BaseModel):
    tag_ids: list[str]


class RepoTagResponse(BaseModel):
    repo_id: str
    tags: list[TagRef]
