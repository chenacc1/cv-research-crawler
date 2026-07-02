"""CrawlKeyword ORM model — user-configurable keywords for crawl filtering."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, String

from app.database import Base


class CrawlKeyword(Base):
    __tablename__ = "crawl_keyword"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    keyword = Column(String(128), nullable=False, unique=True)
    enabled = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
