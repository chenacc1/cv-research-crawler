"""Tests for ArxivCrawler.normalize() and GitHubCrawler.normalize()."""

import pytest

from app.crawlers.arxiv import ArxivCrawler
from app.crawlers.github import GitHubCrawler


class TestArxivCrawlerNormalize:
    """Tests for ArxivCrawler.normalize()."""

    def test_normalize_basic(self):
        crawler = ArxivCrawler()
        raw = {
            "arxiv_id": "2401.12345",
            "title": "Test Paper Title",
            "abstract": "This is a test abstract.",
            "published_date": None,
            "authors": ["Alice", "Bob"],
            "categories": ["cs.CV", "cs.AI"],
            "url": "https://arxiv.org/abs/2401.12345",
            "pdf_url": "https://arxiv.org/pdf/2401.12345.pdf",
        }

        result = crawler.normalize(raw)

        assert result["title"] == "Test Paper Title"
        assert result["source"] == "arxiv"
        assert result["source_id"] == "2401.12345"
        assert result["abstract"] == "This is a test abstract."
        assert result["url"] == "https://arxiv.org/abs/2401.12345"
        assert result["pdf_url"] == "https://arxiv.org/pdf/2401.12345.pdf"
        assert result["code_url"] is None
        assert result["venue"] is None

    def test_normalize_title_normalized_is_stripped(self):
        crawler = ArxivCrawler()
        raw = {
            "arxiv_id": "2401.99999",
            "title": "  A Title With Spaces  ",
            "abstract": "Abstract here.",
            "published_date": None,
            "authors": [],
            "categories": [],
            "url": "https://arxiv.org/abs/2401.99999",
            "pdf_url": None,
        }

        from app.services.paper_service import normalize_title

        result = crawler.normalize(raw)
        expected_normalized = normalize_title(raw["title"])
        assert result["title_normalized"] == expected_normalized
        # Verify normalize_title behavior
        assert result["title_normalized"] == "a title with spaces"

    def test_normalize_missing_fields(self):
        crawler = ArxivCrawler()
        raw = {
            "arxiv_id": "2401.00000",
            "title": "Minimal Paper",
        }

        result = crawler.normalize(raw)

        assert result["title"] == "Minimal Paper"
        assert result["abstract"] == ""
        assert result["url"] == ""
        assert result["pdf_url"] == ""
        assert result["source_id"] == "2401.00000"


class TestGitHubCrawlerNormalize:
    """Tests for GitHubCrawler.normalize()."""

    def test_normalize_basic(self):
        crawler = GitHubCrawler()
        raw = {
            "full_name": "owner/repo",
            "description": "A test repo",
            "html_url": "https://github.com/owner/repo",
            "stargazers_count": 1000,
            "forks_count": 200,
            "language": "Python",
            "topics": ["ml", "cv"],
            "pushed_at": "2024-01-15T10:00:00Z",
        }

        result = crawler.normalize(raw)

        assert result["full_name"] == "owner/repo"
        assert result["description"] == "A test repo"
        assert result["url"] == "https://github.com/owner/repo"
        assert result["stars"] == 1000
        assert result["forks"] == 200
        assert result["language"] == "Python"
        assert result["topics"] == ["ml", "cv"]
        assert result["pushed_at"] is not None

    def test_normalize_missing_fields(self):
        crawler = GitHubCrawler()
        raw = {
            "full_name": "owner/repo",
            "description": "A test repo",
        }

        result = crawler.normalize(raw)

        assert result["full_name"] == "owner/repo"
        assert result["description"] == "A test repo"
        # URL falls back to constructed URL
        assert result["url"] == "https://github.com/owner/repo"
        assert result["stars"] == 0
        assert result["forks"] == 0
        assert result["language"] is None
        assert result["topics"] == []

    def test_normalize_empty_full_name(self):
        crawler = GitHubCrawler()
        raw = {}

        result = crawler.normalize(raw)

        assert result["full_name"] == ""
        assert result["url"] == "https://github.com/"

    def test_parse_datetime_none(self):
        crawler = GitHubCrawler()
        assert crawler._parse_datetime(None) is None

    def test_parse_datetime_invalid(self):
        crawler = GitHubCrawler()
        assert crawler._parse_datetime("not-a-date") is None
