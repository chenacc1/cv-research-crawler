"""APScheduler setup and job registration."""

import asyncio
import logging
from datetime import UTC, datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.crawlers.registry import CrawlerRegistry
from app.database import async_session_factory

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

# Per-source asyncio.Lock to prevent concurrent crawls (replaces plain dict).
_crawler_locks: dict[str, asyncio.Lock] = {}


async def _crawl_job(source: str) -> None:
    """Run a crawler by source name, wrapped in try/except with logging."""
    lock = _crawler_locks.setdefault(source, asyncio.Lock())

    if lock.locked():
        logger.warning(f"Crawler '{source}' is already running. Skipping this run.")
        return

    crawler_cls = CrawlerRegistry.get(source)
    if crawler_cls is None:
        logger.error(f"Unknown crawler source: {source}")
        return

    async with lock:
        try:
            crawler = crawler_cls()
            async with async_session_factory() as db:
                crawl_log = await crawler.run(db)
                await db.commit()
                logger.info(
                    f"Crawler '{source}' completed: "
                    f"status={crawl_log.status}, found={crawl_log.items_found}, "
                    f"new={crawl_log.items_new}, updated={crawl_log.items_updated}"
                )
        except Exception as e:
            logger.exception(f"Crawler '{source}' failed with exception: {e}")


async def _report_job(report_type: str) -> None:
    """Run report generation."""
    from app.engine.report_generator import ReportGenerator

    try:
        async with async_session_factory() as db:
            generator = ReportGenerator(db)
            report = await generator.generate(report_type)
            await db.commit()
            logger.info(
                f"Report '{report_type}' generated: "
                f"papers={report.paper_count}, repos={report.repo_count}, "
                f"path={report.file_path}"
            )
    except Exception as e:
        logger.exception(f"Report '{report_type}' generation failed: {e}")


def setup_scheduler() -> None:
    """Register all scheduled jobs and start the scheduler."""

    # Arxiv crawler
    if settings.crawler_arxiv_enabled:
        scheduler.add_job(
            _crawl_job,
            trigger=IntervalTrigger(minutes=settings.crawler_arxiv_interval_minutes),
            args=["arxiv"],
            id="crawl_arxiv",
            name="Arxiv Crawler",
            replace_existing=True,
        )
        logger.info(f"Registered arxiv crawler job (every {settings.crawler_arxiv_interval_minutes}m)")

    # GitHub crawler
    if settings.crawler_github_enabled:
        scheduler.add_job(
            _crawl_job,
            trigger=IntervalTrigger(minutes=settings.crawler_github_interval_minutes),
            args=["github"],
            id="crawl_github",
            name="GitHub Crawler",
            replace_existing=True,
        )
        logger.info(f"Registered github crawler job (every {settings.crawler_github_interval_minutes}m)")

    # Daily report
    scheduler.add_job(
        _report_job,
        trigger=CronTrigger.from_crontab(settings.report_daily_cron),
        args=["daily"],
        id="report_daily",
        name="Daily Report",
        replace_existing=True,
    )
    logger.info(f"Registered daily report job (cron: {settings.report_daily_cron})")

    # Weekly report
    scheduler.add_job(
        _report_job,
        trigger=CronTrigger.from_crontab(settings.report_weekly_cron),
        args=["weekly"],
        id="report_weekly",
        name="Weekly Report",
        replace_existing=True,
    )
    logger.info(f"Registered weekly report job (cron: {settings.report_weekly_cron})")

    scheduler.start()
    logger.info("Scheduler started with all jobs registered")


def get_scheduler_status() -> list[dict]:
    """Get current status of all registered jobs."""
    # Map job IDs to their config enabled flags
    enabled_map = {
        "crawl_arxiv": settings.crawler_arxiv_enabled,
        "crawl_github": settings.crawler_github_enabled,
        "report_daily": True,
        "report_weekly": True,
    }

    jobs = []
    for job in scheduler.get_jobs():
        job_info = {
            "source": job.id,
            "enabled": enabled_map.get(job.id, True),
            "last_run": job.next_run_time,  # We track last_run via CrawlLog instead
            "next_run": job.next_run_time,
            "last_status": None,
        }

        if isinstance(job.trigger, IntervalTrigger):
            job_info["interval_minutes"] = int(job.trigger.interval.total_seconds() / 60)
        elif isinstance(job.trigger, CronTrigger):
            job_info["cron"] = str(job.trigger)

        jobs.append(job_info)

    return jobs


def is_crawler_running(source: str) -> bool:
    """Check if a crawler is currently running."""
    lock = _crawler_locks.get(source)
    return lock is not None and lock.locked()


async def trigger_crawl(source: str) -> None:
    """Manually trigger a crawl for a given source."""
    lock = _crawler_locks.get(source)
    if lock is not None and lock.locked():
        raise RuntimeError(f"Crawler '{source}' is already running")

    asyncio.create_task(_crawl_job(source))
