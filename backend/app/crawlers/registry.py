"""Crawler registry for plugin-based crawler management."""

from app.crawlers.base import BaseCrawler


class CrawlerRegistry:
    """Singleton registry mapping source names to crawler classes."""

    _crawlers: dict[str, type[BaseCrawler]] = {}

    @classmethod
    def register(cls, crawler_class: type[BaseCrawler]) -> None:
        cls._crawlers[crawler_class.source] = crawler_class

    @classmethod
    def get(cls, source: str) -> type[BaseCrawler] | None:
        return cls._crawlers.get(source)

    @classmethod
    def list_all(cls) -> list[str]:
        return list(cls._crawlers.keys())
