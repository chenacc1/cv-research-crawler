"""Crawl management API endpoints."""

from datetime import UTC, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.crawlers.registry import CrawlerRegistry
from app.database import get_db
from app.engine.scheduler import (
    get_scheduler_status,
    is_crawler_running,
    trigger_crawl,
)
from app.schemas.common import ErrorResponse, PaginatedResponse
from app.schemas.crawl import (
    CrawlLogEntry,
    CrawlStatusJob,
    CrawlStatusResponse,
    CrawlTriggerResponse,
)
from app.services.crawl_service import list_crawl_logs

router = APIRouter(prefix="/api/v1/crawls", tags=["crawls"])


def _log_to_entry(log) -> CrawlLogEntry:
    return CrawlLogEntry(
        id=log.id,
        source=log.source,
        started_at=log.started_at,
        finished_at=log.finished_at,
        items_found=log.items_found,
        items_new=log.items_new,
        items_updated=log.items_updated,
        items_filtered=log.items_filtered,
        items_summarized=log.items_summarized,
        status=log.status,
        error_message=log.error_message,
    )


@router.get("/logs", response_model=PaginatedResponse[CrawlLogEntry])
async def list_crawl_logs_endpoint(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    source: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    sort: str = Query("-started_at"),
    db: AsyncSession = Depends(get_db),
):
    """Paginated crawl log history."""
    logs, total = await list_crawl_logs(
        db,
        page=page,
        page_size=page_size,
        source=source,
        status=status,
        sort=sort,
    )

    items = [_log_to_entry(log) for log in logs]
    pages = max(1, (total + page_size - 1) // page_size)

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/status", response_model=CrawlStatusResponse)
async def get_crawl_status_endpoint(
    db: AsyncSession = Depends(get_db),
):
    """Current scheduler status."""
    from app.services.crawl_service import get_latest_crawl_log

    jobs_raw = get_scheduler_status()
    jobs = []

    for job_raw in jobs_raw:
        source = job_raw["source"]
        last_run = None
        last_status = None

        if source in ("crawl_arxiv", "crawl_github"):
            actual_source = source.replace("crawl_", "")
            latest = await get_latest_crawl_log(db, actual_source)
            if latest:
                last_run = latest.started_at
                last_status = latest.status

        job = CrawlStatusJob(
            source=source,
            enabled=job_raw.get("enabled", True),
            interval_minutes=job_raw.get("interval_minutes"),
            cron=job_raw.get("cron"),
            last_run=last_run,
            next_run=job_raw.get("next_run"),
            last_status=last_status,
        )
        jobs.append(job)

    return CrawlStatusResponse(jobs=jobs)


@router.post(
    "/trigger/{source}",
    response_model=CrawlTriggerResponse,
    status_code=202,
    responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
async def trigger_crawl_endpoint(
    source: str,
):
    """Manually trigger a crawl for a given source."""
    if CrawlerRegistry.get(source) is None:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "CRAWLER_NOT_FOUND", "message": f"Unknown crawler source: {source}", "details": {}}},
        )

    if is_crawler_running(source):
        raise HTTPException(
            status_code=409,
            detail={"error": {"code": "CRAWLER_BUSY", "message": f"Crawler '{source}' is already running", "details": {}}},
        )

    await trigger_crawl(source)

    return CrawlTriggerResponse(
        source=source,
        message=f"Crawl triggered. Check /crawls/logs for results.",
        triggered_at=datetime.now(UTC),
    )
