"""Crawl management business logic."""

from datetime import UTC, date, datetime, timedelta
from typing import Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.crawl_log import CrawlLog
from app.models.paper import Paper
from app.models.repo import GitHubRepo
from app.models.tag import UserTag


async def list_crawl_logs(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    source: str | None = None,
    status: str | None = None,
    sort: str = "-started_at",
) -> tuple[list[CrawlLog], int]:
    """List crawl logs with filters."""
    conditions = []
    if source:
        conditions.append(CrawlLog.source == source)
    if status:
        conditions.append(CrawlLog.status == status)

    base_query = select(CrawlLog)
    if conditions:
        base_query = base_query.where(and_(*conditions))

    # Count
    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Sort
    sort_mapping = {
        "started_at": CrawlLog.started_at.asc(),
        "-started_at": CrawlLog.started_at.desc(),
    }
    order_by = sort_mapping.get(sort, CrawlLog.started_at.desc())

    base_query = base_query.order_by(order_by)
    base_query = base_query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(base_query)
    logs = result.scalars().all()

    return list(logs), total


async def get_latest_crawl_log(db: AsyncSession, source: str, status: str = "success") -> Optional[CrawlLog]:
    """Get the most recent successful crawl log for a source."""
    result = await db.execute(
        select(CrawlLog)
        .where(and_(CrawlLog.source == source, CrawlLog.status == status))
        .order_by(CrawlLog.started_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_stats(db: AsyncSession) -> dict:
    """Compute dashboard statistics."""
    now = datetime.now(UTC)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = today_start - timedelta(days=7)

    # Total papers by source
    source_counts_result = await db.execute(
        select(Paper.source, func.count(Paper.id)).group_by(Paper.source)
    )
    source_counts = {row[0]: row[1] for row in source_counts_result.all()}
    total_papers = sum(source_counts.values())

    # New papers today / this week
    today_count_result = await db.execute(
        select(func.count(Paper.id)).where(Paper.crawled_at >= today_start)
    )
    new_today = today_count_result.scalar() or 0

    week_count_result = await db.execute(
        select(func.count(Paper.id)).where(Paper.crawled_at >= week_ago)
    )
    new_this_week = week_count_result.scalar() or 0

    # Repo stats
    total_repos_result = await db.execute(select(func.count(GitHubRepo.id)))
    total_repos = total_repos_result.scalar() or 0

    repo_today_result = await db.execute(
        select(func.count(GitHubRepo.id)).where(GitHubRepo.crawled_at >= today_start)
    )
    repo_new_today = repo_today_result.scalar() or 0

    repo_week_result = await db.execute(
        select(func.count(GitHubRepo.id)).where(GitHubRepo.crawled_at >= week_ago)
    )
    repo_new_week = repo_week_result.scalar() or 0

    # Tag stats
    total_tags_result = await db.execute(select(func.count(UserTag.id)))
    total_tags = total_tags_result.scalar() or 0

    # Crawl stats
    last_arxiv = await get_latest_crawl_log(db, "arxiv")
    last_github = await get_latest_crawl_log(db, "github")

    total_runs_result = await db.execute(select(func.count(CrawlLog.id)))
    total_runs = total_runs_result.scalar() or 0

    success_runs_result = await db.execute(
        select(func.count(CrawlLog.id)).where(CrawlLog.status == "success")
    )
    success_runs = success_runs_result.scalar() or 0
    success_rate = success_runs / total_runs if total_runs > 0 else 0.0

    # Top categories
    from app.models.category import Category, PaperCategory
    top_cat_result = await db.execute(
        select(Category.name, func.count(PaperCategory.paper_id))
        .join(PaperCategory, Category.id == PaperCategory.category_id)
        .group_by(Category.name)
        .order_by(func.count(PaperCategory.paper_id).desc())
        .limit(10)
    )
    top_categories = [{"name": row[0], "paper_count": row[1]} for row in top_cat_result.all()]

    # Top languages
    top_lang_result = await db.execute(
        select(GitHubRepo.language, func.count(GitHubRepo.id))
        .where(GitHubRepo.language.isnot(None))
        .group_by(GitHubRepo.language)
        .order_by(func.count(GitHubRepo.id).desc())
        .limit(10)
    )
    top_languages = [{"language": row[0], "repo_count": row[1]} for row in top_lang_result.all()]

    # Report counts
    from app.models.report import Report
    daily_count_result = await db.execute(
        select(func.count(Report.id)).where(Report.type == "daily")
    )
    daily_count = daily_count_result.scalar() or 0

    weekly_count_result = await db.execute(
        select(func.count(Report.id)).where(Report.type == "weekly")
    )
    weekly_count = weekly_count_result.scalar() or 0

    return {
        "papers": {
            "total": total_papers,
            "by_source": source_counts,
            "new_today": new_today,
            "new_this_week": new_this_week,
        },
        "repos": {
            "total": total_repos,
            "new_today": repo_new_today,
            "new_this_week": repo_new_week,
        },
        "tags": {"total": total_tags},
        "crawls": {
            "last_arxiv": last_arxiv.finished_at if last_arxiv else None,
            "last_github": last_github.finished_at if last_github else None,
            "total_runs": total_runs,
            "success_rate": round(success_rate, 2),
        },
        "reports": {
            "daily_count": daily_count,
            "weekly_count": weekly_count,
        },
        "top_categories": top_categories,
        "top_languages": top_languages,
    }
