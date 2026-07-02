"""Arxiv API crawler."""

import asyncio
import logging
import re
import xml.etree.ElementTree as ET
from datetime import UTC, datetime

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.crawlers.base import BaseCrawler
from app.models.crawl_log import CrawlLog
from app.services.paper_service import (
    dedup_by_title,
    find_or_create_author,
    find_or_create_category,
    normalize_title,
    upsert_paper,
)
from app.services.keyword_filter import matches_keywords, get_active_keywords
from app.services.llm_service import generate_paper_summary_cn, generate_paper_summary_en

logger = logging.getLogger(__name__)

ARXIV_API_BASE = "http://export.arxiv.org/api/query"
ARXIV_CATEGORIES = ["cs.CV", "cs.AI", "cs.LG", "cs.MM", "cs.CL"]

# Namespace map for Atom XML
ATOM_NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}


async def _summarize_paper(paper, raw: dict) -> None:
    """Background task: generate and save Chinese + English summaries for a paper."""
    import logging as _logging
    _log = _logging.getLogger(__name__)
    try:
        _log.info(f"Summarizing paper: {paper.title[:50]}")
        summary_cn = await generate_paper_summary_cn(paper.title, raw.get("abstract", ""))
        summary_en = await generate_paper_summary_en(paper.title, raw.get("abstract", ""))
        if summary_cn or summary_en:
            from app.database import async_session_factory
            values = {}
            if summary_cn:
                values["summary_cn"] = summary_cn
            if summary_en:
                values["summary_en"] = summary_en
            async with async_session_factory() as sess:
                from sqlalchemy import update
                from app.models.paper import Paper
                await sess.execute(update(Paper).where(Paper.id == paper.id).values(**values))
                await sess.commit()
            _log.info(f"Summary saved for paper: {paper.title[:50]}")
    except Exception as e:
        _log.error(f"Failed to summarize paper {paper.id}: {e}")


class ArxivCrawler(BaseCrawler):
    source = "arxiv"
    delay_seconds = settings.crawler_arxiv_delay_seconds

    async def fetch(self, params: dict) -> list[dict]:
        """Fetch papers from arxiv API for given categories."""
        category = params.get("category", "cs.CV")
        max_results = params.get("max_results", 50)

        url = (
            f"{ARXIV_API_BASE}?search_query=cat:{category}"
            f"&start=0&max_results={max_results}"
            f"&sortBy=submittedDate&sortOrder=descending"
        )

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
            return self._parse_atom(response.text)

    def _parse_atom(self, xml_text: str) -> list[dict]:
        """Parse ATOM XML response into raw item dicts."""
        root = ET.fromstring(xml_text)
        entries = root.findall("atom:entry", ATOM_NS)
        raw_items = []

        for entry in entries:
            # Extract arxiv ID
            arxiv_id_elem = entry.find("atom:id", ATOM_NS)
            arxiv_id = ""
            if arxiv_id_elem is not None and arxiv_id_elem.text:
                # Extract just the ID from the URL
                arxiv_id = arxiv_id_elem.text.split("/abs/")[-1]

            # Title
            title_elem = entry.find("atom:title", ATOM_NS)
            title = title_elem.text.strip() if title_elem is not None and title_elem.text else ""

            # Abstract
            summary_elem = entry.find("atom:summary", ATOM_NS)
            abstract = summary_elem.text.strip() if summary_elem is not None and summary_elem.text else ""

            # Published date
            published_elem = entry.find("atom:published", ATOM_NS)
            published_date = None
            if published_elem is not None and published_elem.text:
                try:
                    published_date = datetime.fromisoformat(
                        published_elem.text.replace("Z", "+00:00")
                    ).date()
                except (ValueError, TypeError):
                    pass

            # Authors
            authors = []
            for author_elem in entry.findall("atom:author", ATOM_NS):
                name_elem = author_elem.find("atom:name", ATOM_NS)
                if name_elem is not None and name_elem.text:
                    authors.append(name_elem.text.strip())

            # Primary category
            primary_cat = entry.find("arxiv:primary_category", ATOM_NS)
            categories = [primary_cat.get("term")] if primary_cat is not None else []

            # Also get all categories
            for cat_elem in entry.findall("atom:category", ATOM_NS):
                cat_term = cat_elem.get("term")
                if cat_term and cat_term not in categories:
                    categories.append(cat_term)

            # Links
            url = ""
            pdf_url = ""
            for link_elem in entry.findall("atom:link", ATOM_NS):
                href = link_elem.get("href", "")
                rel = link_elem.get("rel", "")
                title_attr = link_elem.get("title", "")

                if not url:
                    url = href
                if rel == "related" and "pdf" in (title_attr or "").lower():
                    pdf_url = href
                elif not pdf_url and href.endswith(".pdf"):
                    pdf_url = href

            if not url and arxiv_id:
                url = f"https://arxiv.org/abs/{arxiv_id}"
            if not pdf_url and arxiv_id:
                pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

            raw_items.append({
                "arxiv_id": arxiv_id,
                "title": title,
                "abstract": abstract,
                "published_date": published_date,
                "authors": authors,
                "categories": categories,
                "url": url,
                "pdf_url": pdf_url,
            })

        return raw_items

    def normalize(self, raw: dict) -> dict:
        """Convert arxiv raw item to Paper model dict."""
        return {
            "title": raw["title"],
            "title_normalized": normalize_title(raw["title"]),
            "abstract": raw.get("abstract", ""),
            "url": raw.get("url", ""),
            "pdf_url": raw.get("pdf_url", ""),
            "code_url": None,
            "source": self.source,
            "source_id": raw.get("arxiv_id", ""),
            "venue": None,
            "published_date": raw.get("published_date"),
        }

    async def run(self, db: AsyncSession) -> CrawlLog:
        """Run the arxiv crawl: fetch -> normalize -> upsert -> log."""
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
        items_summarized = 0

        keywords = await get_active_keywords(db)

        try:
            for category in ARXIV_CATEGORIES:
                logger.info(f"Fetching arxiv category: {category}")
                try:
                    raw_items = await self.fetch({"category": category, "max_results": 50})
                except Exception as e:
                    logger.error(f"Failed to fetch arxiv category {category}: {e}")
                    continue

                for raw in raw_items:
                    try:
                        paper_data = self.normalize(raw)

                        # Keyword filtering
                        search_text = f"{paper_data['title']} {raw.get('abstract', '')}"
                        if not matches_keywords([search_text], keywords):
                            items_filtered += 1
                            continue

                        paper, is_new = await upsert_paper(db, paper_data)
                        items_found += 1
                        if is_new:
                            items_new += 1
                        else:
                            items_updated += 1

                        # Handle authors
                        for i, author_name in enumerate(raw.get("authors", [])):
                            author = await find_or_create_author(db, author_name)
                            # Check if PaperAuthor already exists
                            from sqlalchemy import and_, select
                            from app.models.author import PaperAuthor
                            pa_result = await db.execute(
                                select(PaperAuthor).where(
                                    and_(
                                        PaperAuthor.paper_id == paper.id,
                                        PaperAuthor.author_id == author.id,
                                    )
                                )
                            )
                            if pa_result.scalar_one_or_none() is None:
                                db.add(PaperAuthor(
                                    paper_id=paper.id,
                                    author_id=author.id,
                                    author_order=i,
                                ))

                        # Handle categories
                        for cat_name in raw.get("categories", []):
                            category_obj = await find_or_create_category(db, cat_name, self.source)
                            from sqlalchemy import and_, select
                            from app.models.category import PaperCategory
                            pc_result = await db.execute(
                                select(PaperCategory).where(
                                    and_(
                                        PaperCategory.paper_id == paper.id,
                                        PaperCategory.category_id == category_obj.id,
                                    )
                                )
                            )
                            if pc_result.scalar_one_or_none() is None:
                                db.add(PaperCategory(
                                    paper_id=paper.id,
                                    category_id=category_obj.id,
                                ))

                        # Title dedup
                        await dedup_by_title(db, paper)

                    except Exception as e:
                        logger.error(f"Failed to process arxiv paper {raw.get('arxiv_id')}: {e}")

                # Polite delay between categories
                await asyncio.sleep(self.delay_seconds)

            # Generate AI summaries for newest papers without summaries (batch of 5)
            if settings.llm_summary_enabled:
                from sqlalchemy import select
                from app.models.paper import Paper as PaperModel
                result = await db.execute(
                    select(PaperModel).where(
                        PaperModel.summary_cn.is_(None),
                        PaperModel.summary_en.is_(None),
                    ).order_by(PaperModel.crawled_at.desc()).limit(5)
                )
                papers_to_summarize = result.scalars().all()
                if papers_to_summarize:
                    logger.info(f"Generating summaries for {len(papers_to_summarize)} papers")
                for p in papers_to_summarize:
                    try:
                        summary_cn = await generate_paper_summary_cn(p.title, p.abstract or "")
                        summary_en = await generate_paper_summary_en(p.title, p.abstract or "")
                        if summary_cn:
                            p.summary_cn = summary_cn
                        if summary_en:
                            p.summary_en = summary_en
                        if summary_cn or summary_en:
                            items_summarized += 1
                            logger.info(f"Summary done for: {p.title[:40]}")
                    except Exception:
                        pass
                await db.flush()

            crawl_log.status = "success"

        except Exception as e:
            logger.exception(f"Arxiv crawl failed: {e}")
            crawl_log.status = "failed"
            crawl_log.error_message = str(e)

        finally:
            crawl_log.finished_at = datetime.now(UTC)
            crawl_log.items_found = items_found
            crawl_log.items_new = items_new
            crawl_log.items_updated = items_updated
            crawl_log.items_filtered = items_filtered
            crawl_log.items_summarized = items_summarized

        return crawl_log
