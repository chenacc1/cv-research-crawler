"""Paper Pydantic schemas."""

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import TagRef


class CategoryRef(BaseModel):
    id: str
    name: str
    source: str

    model_config = {"from_attributes": True}


class AuthorRef(BaseModel):
    id: str
    name: str
    affiliation: Optional[str] = None
    author_order: int = 0

    model_config = {"from_attributes": True}


class PaperVersionRef(BaseModel):
    id: str
    title: str
    source: str
    url: str

    model_config = {"from_attributes": True}


class PaperSummary(BaseModel):
    id: str
    title: str
    source: str
    source_id: str
    venue: Optional[str] = None
    published_date: Optional[date] = None
    url: str
    pdf_url: Optional[str] = None
    code_url: Optional[str] = None
    crawled_at: datetime
    updated_at: datetime
    categories: list[CategoryRef] = Field(default_factory=list)
    tags: list[TagRef] = Field(default_factory=list)
    author_names: list[str] = Field(default_factory=list)
    summary_cn: Optional[str] = None
    summary_en: Optional[str] = None

    model_config = {"from_attributes": True}


class PaperDetail(PaperSummary):
    abstract: Optional[str] = None
    authors: list[AuthorRef] = Field(default_factory=list)
    merged_into_id: Optional[str] = None
    versions: list[PaperVersionRef] = Field(default_factory=list)


class PaperTagUpdate(BaseModel):
    tag_ids: list[str]


class PaperTagResponse(BaseModel):
    paper_id: str
    tags: list[TagRef]
