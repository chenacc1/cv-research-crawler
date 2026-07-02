"""Report generation engine: query DB, render Jinja2, write file."""

import logging
import os
from datetime import UTC, date, datetime, timedelta

from jinja2 import Environment, FileSystemLoader
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models.category import Category, PaperCategory
from app.models.paper import Paper
from app.models.repo import GitHubRepo
from app.models.report import Report

logger = logging.getLogger(__name__)

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")


class ReportGenerator:
    """Generate daily and weekly Markdown reports."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.jinja_env = Environment(
            loader=FileSystemLoader(TEMPLATE_DIR),
            autoescape=False,
        )

    async def generate(
        self,
        report_type: str,
        date_range_start: date | None = None,
        date_range_end: date | None = None,
    ) -> Report:
        """Generate a report of the given type ('daily' or 'weekly').

        Args:
            report_type: 'daily' or 'weekly'
            date_range_start: Optional override for the start date.
            date_range_end: Optional override for the end date.
        """
        now = datetime.now(UTC)

        if date_range_start is not None and date_range_end is not None:
            date_start = date_range_start
            date_end = date_range_end
        elif report_type == "daily":
            date_start = now.date()
            date_end = now.date()
        elif report_type == "weekly":
            # Last Monday to Sunday
            days_since_monday = now.weekday()
            last_monday = now.date() - timedelta(days=days_since_monday)
            date_start = last_monday
            date_end = last_monday + timedelta(days=6)
        else:
            raise ValueError(f"Unknown report type: {report_type}")

        # Collect papers in date range
        papers = await self._get_papers(
            date_start, date_end,
            limit=30 if report_type == "weekly" else 20,
            group_by_category=(report_type == "daily"),
        )

        # Collect repos
        repos = await self._get_repos(
            date_start, date_end,
            limit=10,
            by_star_gain=(report_type == "weekly"),
        )

        # Stats
        stats = await self._get_stats(date_start, date_end, report_type)

        # Render template
        template = self.jinja_env.get_template(f"{report_type}.md.j2")
        content = template.render(
            papers=papers,
            repos=repos,
            stats=stats,
            date_range_start=date_start,
            date_range_end=date_end,
            generated_at=now.isoformat(),
        )

        # Ensure output directory
        os.makedirs(settings.report_output_dir, exist_ok=True)

        # Write file with exact timestamp to avoid overwriting previous runs.
        ts = now.strftime("%Y%m%dT%H%M%S")
        filename = f"{report_type}-{date_end}-{ts}.md"
        file_path = os.path.join(settings.report_output_dir, filename)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        # Calculate total paper count from grouped or flat data
        if isinstance(papers, list):
            paper_count = len(papers)
        else:
            paper_count = sum(len(cat["papers"]) for cat in papers.get("categories", []))

        # Save Report record
        report = Report(
            type=report_type,
            date_range_start=date_start,
            date_range_end=date_end,
            file_path=file_path,
            paper_count=paper_count,
            repo_count=len(repos),
            delivery_status="delivered",
        )
        self.db.add(report)
        await self.db.flush()

        logger.info(f"Report generated: {file_path}")
        return report

    async def _get_papers(
        self,
        start: date,
        end: date,
        limit: int = 20,
        group_by_category: bool = False,
    ) -> list[dict] | dict:
        """Get top papers in date range.

        When group_by_category is True, returns a dict suitable for
        category-grouped rendering:
            {"categories": [{"name": "...", "papers": [paper_dict, ...]}, ...]}
        Otherwise returns a flat list of paper dicts.
        """
        result = await self.db.execute(
            select(Paper)
            .where(
                Paper.published_date >= start,
                Paper.published_date <= end,
                Paper.merged_into_id.is_(None),
            )
            .options(
                selectinload(Paper.categories).joinedload(PaperCategory.category),
            )
            .order_by(desc(Paper.crawled_at))
            .limit(limit * 5 if group_by_category else limit)  # Fetch more for grouping
        )
        papers = result.unique().scalars().all()

        if not group_by_category:
            paper_dicts = []
            for p in papers[:limit]:
                paper_dicts.append(self._paper_to_dict(p))
            return paper_dicts

        # Group by category, take top N per category
        from collections import defaultdict
        categorized: dict[str, list] = defaultdict(list)
        uncategorized: list = []

        for p in papers:
            cat_names = [
                pc.category.name
                for pc in p.categories
                if pc.category is not None
            ]
            if not cat_names:
                uncategorized.append(self._paper_to_dict(p))
            else:
                for cn in cat_names:
                    categorized[cn].append(self._paper_to_dict(p))

        # Sort categories by number of papers (desc), then take top N per category
        sorted_categories = sorted(categorized.items(), key=lambda x: len(x[1]), reverse=True)
        categories_list = []
        for cat_name, cat_papers in sorted_categories:
            # Deduplicate papers that appear in multiple categories
            seen = set()
            unique_papers = []
            for pdict in cat_papers:
                if pdict["id"] not in seen:
                    seen.add(pdict["id"])
                    unique_papers.append(pdict)
            categories_list.append({
                "name": cat_name,
                "papers": unique_papers[:limit],
            })

        # Add uncategorized
        if uncategorized:
            seen = set()
            unique_uncat = []
            for pdict in uncategorized:
                if pdict["id"] not in seen:
                    seen.add(pdict["id"])
                    unique_uncat.append(pdict)
            categories_list.append({
                "name": "Other",
                "papers": unique_uncat[:limit],
            })

        return {"categories": categories_list}

    def _paper_to_dict(self, p: Paper) -> dict:
        """Convert a Paper ORM instance to a dict for template rendering."""
        return {
            "id": p.id,
            "title": p.title,
            "source": p.source,
            "source_id": p.source_id,
            "url": p.url,
            "code_url": p.code_url,
            "published_date": p.published_date,
            "venue": p.venue,
        }

    async def _get_repos(
        self,
        start: date,
        end: date,
        limit: int = 10,
        by_star_gain: bool = False,
    ) -> list[dict]:
        """Get trending repos in date range.

        When by_star_gain is True, sorts by (stars - previous_stars) descending
        for "rising repos". Otherwise sorts by absolute stars.
        """
        start_dt = datetime(start.year, start.month, start.day, tzinfo=UTC)
        end_dt = datetime(end.year, end.month, end.day, 23, 59, 59, tzinfo=UTC)

        result = await self.db.execute(
            select(GitHubRepo)
            .where(GitHubRepo.crawled_at >= start_dt, GitHubRepo.crawled_at <= end_dt)
            .order_by(
                desc(GitHubRepo.stars - GitHubRepo.previous_stars)
                if by_star_gain
                else desc(GitHubRepo.stars)
            )
            .limit(limit)
        )
        repos = result.scalars().all()

        return [
            {
                "id": r.id,
                "full_name": r.full_name,
                "description": r.description,
                "url": r.url,
                "stars": r.stars,
                "star_gain": r.stars - r.previous_stars,
                "forks": r.forks,
                "language": r.language,
                "topics": r.topics or [],
                "pushed_at": r.pushed_at,
            }
            for r in repos
        ]

    async def _get_stats(self, start: date, end: date, report_type: str = "daily") -> dict:
        """Get category breakdown and other stats for the period.

        For weekly reports, includes week-over-week delta per category.
        """
        # Total paper count
        paper_count_result = await self.db.execute(
            select(func.count(Paper.id)).where(
                Paper.published_date >= start,
                Paper.published_date <= end,
            )
        )
        paper_count = paper_count_result.scalar() or 0

        # Total repo count
        repo_count_result = await self.db.execute(
            select(func.count(GitHubRepo.id)).where(
                GitHubRepo.crawled_at >= datetime(start.year, start.month, start.day, tzinfo=UTC),
            )
        )
        repo_count = repo_count_result.scalar() or 0

        # Per-category paper counts
        cat_result = await self.db.execute(
            select(
                Category.name,
                func.count(Paper.id).label("count"),
            )
            .join(PaperCategory, PaperCategory.category_id == Category.id)
            .join(Paper, Paper.id == PaperCategory.paper_id)
            .where(
                Paper.published_date >= start,
                Paper.published_date <= end,
            )
            .group_by(Category.name)
            .order_by(desc(func.count(Paper.id)))
        )
        rows = cat_result.all()
        categories = [{"name": row.name, "count": row.count} for row in rows]

        stats = {
            "paper_count": paper_count,
            "repo_count": repo_count,
            "categories": categories,
            "date_range_start": start,
            "date_range_end": end,
        }

        # Week-over-week delta for weekly reports
        if report_type == "weekly":
            prev_start = start - timedelta(days=7)
            prev_end = end - timedelta(days=7)

            prev_cat_result = await self.db.execute(
                select(
                    Category.name,
                    func.count(Paper.id).label("count"),
                )
                .join(PaperCategory, PaperCategory.category_id == Category.id)
                .join(Paper, Paper.id == PaperCategory.paper_id)
                .where(
                    Paper.published_date >= prev_start,
                    Paper.published_date <= prev_end,
                )
                .group_by(Category.name)
            )
            prev_rows = {row.name: row.count for row in prev_cat_result.all()}

            for cat in categories:
                prev_count = prev_rows.get(cat["name"], 0)
                cat["prev_week_count"] = prev_count
                cat["delta"] = cat["count"] - prev_count

        return stats
