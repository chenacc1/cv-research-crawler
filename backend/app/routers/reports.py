"""Report API endpoints."""

import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.common import ErrorResponse, PaginatedResponse
from app.schemas.report import ReportDetail, ReportSummary
from app.services.report_service import get_report, list_reports

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


def _report_to_summary(report) -> ReportSummary:
    return ReportSummary(
        id=report.id,
        type=report.type,
        date_range_start=report.date_range_start,
        date_range_end=report.date_range_end,
        file_path=report.file_path,
        paper_count=report.paper_count,
        repo_count=report.repo_count,
        delivery_status=report.delivery_status,
        generated_at=report.generated_at,
    )


def _report_to_detail(report) -> ReportDetail:
    content = ""
    if os.path.exists(report.file_path):
        with open(report.file_path, "r", encoding="utf-8") as f:
            content = f.read()

    return ReportDetail(
        id=report.id,
        type=report.type,
        date_range_start=report.date_range_start,
        date_range_end=report.date_range_end,
        file_path=report.file_path,
        paper_count=report.paper_count,
        repo_count=report.repo_count,
        delivery_status=report.delivery_status,
        generated_at=report.generated_at,
        content=content,
    )


@router.get("", response_model=PaginatedResponse[ReportSummary])
async def list_reports_endpoint(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    type: Optional[str] = Query(None),
    sort: str = Query("-generated_at"),
    db: AsyncSession = Depends(get_db),
):
    """List generated reports."""
    reports, total = await list_reports(
        db,
        page=page,
        page_size=page_size,
        type_filter=type,
        sort=sort,
    )

    items = [_report_to_summary(r) for r in reports]
    pages = max(1, (total + page_size - 1) // page_size)

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/{report_id}", response_model=ReportDetail, responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def get_report_endpoint(
    report_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get report metadata plus rendered Markdown content."""
    report = await get_report(db, report_id)
    if report is None:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "RESOURCE_NOT_FOUND", "message": f"Report with id {report_id} not found", "details": {}}},
        )

    if not os.path.exists(report.file_path):
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "INTERNAL_ERROR", "message": f"Report file missing from disk: {report.file_path}", "details": {}}},
        )

    return _report_to_detail(report)


@router.post("/{report_id}/retry", response_model=ReportDetail, responses={404: {"model": ErrorResponse}})
async def retry_report_endpoint(
    report_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Regenerate a specific report for its original date range."""
    report = await get_report(db, report_id)
    if report is None:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "RESOURCE_NOT_FOUND", "message": f"Report with id {report_id} not found", "details": {}}},
        )

    from app.engine.report_generator import ReportGenerator

    generator = ReportGenerator(db)
    new_report = await generator.generate(
        report.type,
        date_range_start=report.date_range_start,
        date_range_end=report.date_range_end,
    )
    await db.flush()

    return _report_to_detail(new_report)
