"""System stats Pydantic schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PaperStats(BaseModel):
    total: int
    by_source: dict[str, int]
    new_today: int
    new_this_week: int


class RepoStats(BaseModel):
    total: int
    new_today: int
    new_this_week: int


class TagStats(BaseModel):
    total: int


class CrawlStats(BaseModel):
    last_arxiv: Optional[datetime] = None
    last_github: Optional[datetime] = None
    total_runs: int
    success_rate: float


class ReportStats(BaseModel):
    daily_count: int
    weekly_count: int


class CategoryCount(BaseModel):
    name: str
    paper_count: int


class LanguageCount(BaseModel):
    language: str
    repo_count: int


class StatsResponse(BaseModel):
    papers: PaperStats
    repos: RepoStats
    tags: TagStats
    crawls: CrawlStats
    reports: ReportStats
    top_categories: list[CategoryCount]
    top_languages: list[LanguageCount]


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    database: str
    scheduler: str
    version: str
