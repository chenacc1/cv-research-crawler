"""Base crawler abstract class."""

from abc import ABC, abstractmethod

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.crawl_log import CrawlLog


class BaseCrawler(ABC):
    """All crawlers implement this interface."""

    source: str = "unknown"
    delay_seconds: float = 1.0

    @abstractmethod
    async def fetch(self, params: dict) -> list[dict]:
        """Fetch raw data from the source API. Returns a list of raw item dicts."""
        ...

    @abstractmethod
    def normalize(self, raw: dict) -> dict:
        """Convert one raw item into the unified model dict."""
        ...

    @abstractmethod
    async def run(self, db: AsyncSession) -> CrawlLog:
        """Template method: fetch -> normalize -> upsert -> log."""
        ...
