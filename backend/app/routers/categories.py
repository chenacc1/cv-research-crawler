"""Categories API endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.category import Category, PaperCategory
from app.schemas.paper import CategoryRef

router = APIRouter(prefix="/api/v1/categories", tags=["categories"])


@router.get("")
async def list_categories_endpoint(
    source: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List all distinct categories, optionally filtered by source."""
    conditions = []
    if source:
        conditions.append(Category.source == source)

    base_query = select(
        Category.id,
        Category.name,
        Category.source,
        func.count(PaperCategory.paper_id).label("paper_count"),
    ).outerjoin(PaperCategory, Category.id == PaperCategory.category_id)

    if conditions:
        from sqlalchemy import and_
        base_query = base_query.where(and_(*conditions))

    base_query = base_query.group_by(Category.id).order_by(func.count(PaperCategory.paper_id).desc())

    result = await db.execute(base_query)
    rows = result.all()

    items = [
        {
            "id": row[0],
            "name": row[1],
            "source": row[2],
            "paper_count": row[3],
        }
        for row in rows
    ]

    return {"items": items}
