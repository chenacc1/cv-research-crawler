"""Authors API endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.database import get_db
from app.models.author import Author, PaperAuthor
from app.models.paper import Paper
from app.schemas.common import ErrorResponse, PaginatedResponse

router = APIRouter(prefix="/api/v1/authors", tags=["authors"])


@router.get("")
async def list_authors_endpoint(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    q: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List authors with search and pagination."""
    conditions = []
    if q:
        conditions.append(Author.name.ilike(f"%{q}%"))

    base_query = select(Author)
    if conditions:
        base_query = base_query.where(or_(*conditions))

    # Count
    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    base_query = base_query.order_by(Author.name)
    base_query = base_query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(base_query)
    authors = result.scalars().all()

    # Get paper counts for ALL authors in a single query (avoids N+1).
    author_ids = [a.id for a in authors]
    paper_counts: dict[str, int] = {}
    if author_ids:
        pc_result = await db.execute(
            select(
                PaperAuthor.author_id,
                func.count(PaperAuthor.paper_id).label("cnt"),
            )
            .where(PaperAuthor.author_id.in_(author_ids))
            .group_by(PaperAuthor.author_id)
        )
        for row in pc_result:
            paper_counts[row.author_id] = row.cnt

    items = []
    for author in authors:
        items.append({
            "id": author.id,
            "name": author.name,
            "affiliation": author.affiliation,
            "paper_count": paper_counts.get(author.id, 0),
        })

    pages = max(1, (total + page_size - 1) // page_size)

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages,
    }


@router.get("/{author_id}", responses={404: {"model": ErrorResponse}})
async def get_author_endpoint(
    author_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a single author with their papers."""
    result = await db.execute(
        select(Author)
        .where(Author.id == author_id)
        .options(
            selectinload(Author.papers).joinedload(PaperAuthor.paper),
        )
    )
    author = result.unique().scalar_one_or_none()

    if author is None:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "RESOURCE_NOT_FOUND", "message": f"Author with id {author_id} not found", "details": {}}},
        )

    papers = []
    for pa in sorted(author.papers, key=lambda x: x.author_order):
        papers.append({
            "id": pa.paper.id if pa.paper else "",
            "title": pa.paper.title if pa.paper else "",
            "published_date": pa.paper.published_date if pa.paper else None,
            "source": pa.paper.source if pa.paper else "",
            "author_order": pa.author_order,
        })

    return {
        "id": author.id,
        "name": author.name,
        "affiliation": author.affiliation,
        "papers": papers,
    }
