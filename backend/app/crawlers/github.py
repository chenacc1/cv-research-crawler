"""GitHub API crawler."""

import asyncio
import logging
import random
import re
from datetime import UTC, datetime

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.crawlers.base import BaseCrawler
from app.models.crawl_log import CrawlLog
from app.services.repo_service import upsert_repo
from app.services.keyword_filter import matches_keywords, get_active_keywords
from app.services.llm_service import generate_repo_summary_cn, generate_repo_summary_en

logger = logging.getLogger(__name__)

GITHUB_API_BASE = "https://api.github.com"
GITHUB_TRENDING_URL = "https://github.com/trending/python?since=daily"
GITHUB_SEARCH_TOPICS = [
    "computer-vision",
    "deep-learning",
    "object-detection",
    "image-segmentation",
    "generative-models",
    "nerf",
    "3d-vision",
    "multimodal",
    "video-understanding",
]


async def _summarize_repo(repo, raw: dict) -> None:
    """Background task: generate and save Chinese + English summaries for a repo."""
    try:
        desc = raw.get("description", "")
        topics_list = raw.get("topics", [])
        summary_cn = await generate_repo_summary_cn(repo.full_name, desc, topics_list)
        summary_en = await generate_repo_summary_en(repo.full_name, desc, topics_list)
        if summary_cn or summary_en:
            from app.database import async_session_factory
            values = {}
            if summary_cn:
                values["summary_cn"] = summary_cn
            if summary_en:
                values["summary_en"] = summary_en
            async with async_session_factory() as sess:
                from sqlalchemy import update
                from app.models.repo import GitHubRepo
                await sess.execute(update(GitHubRepo).where(GitHubRepo.id == repo.id).values(**values))
                await sess.commit()
    except Exception:
        pass


class GitHubCrawler(BaseCrawler):
    source = "github"
    delay_seconds = settings.crawler_github_delay_seconds

    def _headers(self) -> dict:
        headers = {
            "Accept": "application/vnd.github.v3+json",
        }
        if settings.github_token:
            headers["Authorization"] = f"Bearer {settings.github_token}"
        return headers

    async def _request_with_backoff(self, client: httpx.AsyncClient, url: str, params: dict) -> dict:
        """Make a GitHub API request with exponential backoff for 429."""
        max_retries = 5
        base_delay = 1.0

        for attempt in range(max_retries):
            response = await client.get(url, params=params, headers=self._headers())

            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                if retry_after:
                    delay = float(retry_after)
                else:
                    delay = min(base_delay * (2 ** attempt) + random.uniform(0, 1), 60.0)
                logger.warning(f"GitHub API rate limited. Retrying in {delay:.1f}s (attempt {attempt + 1}/{max_retries})")
                await asyncio.sleep(delay)
                continue

            if response.status_code == 403 and "rate limit" in response.text.lower():
                retry_after = response.headers.get("Retry-After", "60")
                delay = float(retry_after)
                logger.warning(f"GitHub secondary rate limit. Retrying in {delay:.1f}s")
                await asyncio.sleep(delay)
                continue

            response.raise_for_status()
            return response.json()

        raise Exception(f"GitHub API rate limit exceeded after {max_retries} retries")

    async def fetch(self, params: dict) -> list[dict]:
        """Fetch repos from GitHub search API for given topic."""
        topic = params.get("topic", "")
        per_page = params.get("per_page", 30)

        all_items = []
        async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
            for page in range(1, 4):  # Max 3 pages per topic
                url = f"{GITHUB_API_BASE}/search/repositories"
                query_params = {
                    "q": f"topic:{topic}",
                    "sort": "updated",
                    "order": "desc",
                    "per_page": per_page,
                    "page": page,
                }

                try:
                    data = await self._request_with_backoff(client, url, query_params)
                    items = data.get("items", [])
                    all_items.extend(items)

                    if len(items) < per_page:
                        break  # No more pages

                except Exception as e:
                    logger.error(f"GitHub search failed for topic '{topic}' page {page}: {e}")
                    break

                await asyncio.sleep(self.delay_seconds)

        return all_items

    async def fetch_trending(self, language: str = "python", since: str = "daily") -> list[str]:
        """Scrape GitHub Trending page and return list of full_name strings.

        Parses the HTML to extract repo names from the trending page,
        then each can be enriched with API data via the main fetch flow.
        """
        url = f"https://github.com/trending/{language}?since={since}"
        repo_names = []

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True, verify=False) as client:
            try:
                response = await client.get(url, headers={
                    "Accept": "text/html",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                })
                response.raise_for_status()
            except Exception as e:
                logger.error(f"Failed to fetch GitHub Trending page: {e}")
                return repo_names

            html = response.text

            # Parse repo names from the trending page
            # Trending repos are listed in <h2> elements with links like /owner/repo
            pattern = re.compile(r'<h2[^>]*>\s*<a[^>]*href="/([^/"]+/[^/"]+)"[^>]*>', re.IGNORECASE)
            matches = pattern.findall(html)

            seen = set()
            for match in matches:
                # Filter out non-repo links (e.g., /trending, /topics, etc.)
                parts = match.split("/")
                if len(parts) == 2 and match not in seen:
                    seen.add(match)
                    repo_names.append(match)

            logger.info(f"Found {len(repo_names)} trending repos on GitHub Trending page")

        return repo_names

    def normalize(self, raw: dict) -> dict:
        """Convert GitHub API repo item to GitHubRepo model dict."""
        return {
            "full_name": raw.get("full_name", ""),
            "description": raw.get("description", ""),
            "url": raw.get("html_url", f"https://github.com/{raw.get('full_name', '')}"),
            "stars": raw.get("stargazers_count", 0),
            "forks": raw.get("forks_count", 0),
            "language": raw.get("language"),
            "topics": raw.get("topics", []),
            "pushed_at": self._parse_datetime(raw.get("pushed_at")),
        }

    def _parse_datetime(self, dt_str: str | None) -> datetime | None:
        """Parse GitHub datetime string."""
        if not dt_str:
            return None
        try:
            return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None

    async def run(self, db: AsyncSession) -> CrawlLog:
        """Run the GitHub crawl: fetch -> normalize -> upsert -> log."""
        crawl_log = CrawlLog(
            source=self.source,
            started_at=datetime.now(UTC),
            status="running",
        )
        db.add(crawl_log)
        await db.flush()

        items_found = 0
        items_new = 0
        items_updated = 0
        items_filtered = 0

        keywords = await get_active_keywords(db)

        try:
            seen_full_names = set()

            for topic in GITHUB_SEARCH_TOPICS:
                logger.info(f"Fetching GitHub topic: {topic}")
                try:
                    raw_items = await self.fetch({"topic": topic, "per_page": 30})
                except Exception as e:
                    logger.error(f"Failed to fetch GitHub topic {topic}: {e}")
                    continue

                for raw in raw_items:
                    try:
                        full_name = raw.get("full_name", "")
                        if full_name in seen_full_names:
                            continue
                        seen_full_names.add(full_name)

                        repo_data = self.normalize(raw)
                        repo_data["crawled_at"] = datetime.now(UTC)
                        repo_data["last_crawled_at"] = datetime.now(UTC)

                        # Keyword filtering
                        desc = raw.get("description", "")
                        topics_list = raw.get("topics", [])
                        search_text = f"{repo_data['full_name']} {desc} {' '.join(topics_list)}"
                        if not matches_keywords([search_text], keywords):
                            items_filtered += 1
                            continue

                        repo, is_new = await upsert_repo(db, repo_data)
                        items_found += 1
                        if is_new:
                            items_new += 1
                        else:
                            items_updated += 1

                        asyncio.create_task(_summarize_repo(repo, raw))

                    except Exception as e:
                        logger.error(f"Failed to process GitHub repo {raw.get('full_name')}: {e}")

                # Polite delay between topics
                await asyncio.sleep(self.delay_seconds)

            # Fetch trending repos and enrich with API data
            logger.info("Fetching GitHub Trending repos...")
            try:
                trending_names = await self.fetch_trending("python", "daily")
                async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
                    for full_name in trending_names:
                        if full_name in seen_full_names:
                            continue
                        seen_full_names.add(full_name)

                        try:
                            repo_url = f"{GITHUB_API_BASE}/repos/{full_name}"
                            raw = await self._request_with_backoff(client, repo_url, {})
                        except Exception as e:
                            logger.error(f"Failed to fetch trending repo {full_name}: {e}")
                            continue

                        repo_data = self.normalize(raw)
                        repo_data["crawled_at"] = datetime.now(UTC)
                        repo_data["last_crawled_at"] = datetime.now(UTC)

                        # Keyword filtering
                        desc = raw.get("description", "")
                        topics_list = raw.get("topics", [])
                        search_text = f"{repo_data['full_name']} {desc} {' '.join(topics_list)}"
                        if not matches_keywords([search_text], keywords):
                            items_filtered += 1
                            continue

                        repo, is_new = await upsert_repo(db, repo_data)
                        items_found += 1
                        if is_new:
                            items_new += 1
                        else:
                            items_updated += 1

                        asyncio.create_task(_summarize_repo(repo, raw))

                        await asyncio.sleep(self.delay_seconds)
            except Exception as e:
                logger.warning(f"Failed to fetch trending repos: {e}")

            crawl_log.status = "success"

        except Exception as e:
            logger.exception(f"GitHub crawl failed: {e}")
            crawl_log.status = "failed"
            crawl_log.error_message = str(e)

        finally:
            crawl_log.finished_at = datetime.now(UTC)
            crawl_log.items_found = items_found
            crawl_log.items_new = items_new
            crawl_log.items_updated = items_updated
            crawl_log.items_filtered = items_filtered

        return crawl_log
