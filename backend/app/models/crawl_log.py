"""CrawlLog ORM model."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Index, Integer, String, Text

from app.database import Base


class CrawlLog(Base):
    __tablename__ = "crawl_log"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source = Column(String(32), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=False)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    items_found = Column(Integer, default=0)
    items_new = Column(Integer, default=0)
    items_updated = Column(Integer, default=0)
    items_filtered = Column(Integer, default=0)
    items_summarized = Column(Integer, default=0)
    status = Column(String(16), nullable=False, default="running")
    error_message = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_crawl_log_source_started", source, started_at.desc()),
    )
