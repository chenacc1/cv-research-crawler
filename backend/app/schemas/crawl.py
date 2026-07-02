"""Crawl Pydantic schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CrawlLogEntry(BaseModel):
    id: str
    source: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    items_found: int
    items_new: int
    items_updated: int
    items_filtered: int = 0
    items_summarized: int = 0
    status: str
    error_message: Optional[str] = None

    model_config = {"from_attributes": True}


class CrawlStatusJob(BaseModel):
    source: str
    enabled: bool
    interval_minutes: Optional[int] = None
    cron: Optional[str] = None
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    last_status: Optional[str] = None


class CrawlStatusResponse(BaseModel):
    jobs: list[CrawlStatusJob]


class CrawlTriggerResponse(BaseModel):
    source: str
    message: str
    triggered_at: datetime
