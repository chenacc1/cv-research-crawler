"""Crawler plugin system initialization."""

from app.crawlers.base import BaseCrawler
from app.crawlers.registry import CrawlerRegistry
from app.crawlers.arxiv import ArxivCrawler
from app.crawlers.github import GitHubCrawler

# Register all crawlers at import time
CrawlerRegistry.register(ArxivCrawler)
CrawlerRegistry.register(GitHubCrawler)

__all__ = ["BaseCrawler", "CrawlerRegistry", "ArxivCrawler", "GitHubCrawler"]
