"""Report business logic."""

from datetime import date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.report import Report


async def list_reports(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    type_filter: str | None = None,
    sort: str = "-generated_at",
) -> tuple[list[Report], int]:
    """List reports with optional type filter."""
    conditions = []
    if type_filter:
        conditions.append(Report.type == type_filter)

    base_query = select(Report)
    if conditions:
        from sqlalchemy import and_
        base_query = base_query.where(and_(*conditions))

    # Count
    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Sort
    sort_mapping = {
        "generated_at": Report.generated_at.asc(),
        "-generated_at": Report.generated_at.desc(),
    }
    order_by = sort_mapping.get(sort, Report.generated_at.desc())

    base_query = base_query.order_by(order_by)
    base_query = base_query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(base_query)
    reports = result.scalars().all()

    return list(reports), total


async def get_report(db: AsyncSession, report_id: str) -> Report | None:
    """Get a single report by ID."""
    result = await db.execute(select(Report).where(Report.id == report_id))
    return result.scalar_one_or_none()
