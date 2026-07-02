"""Paper API endpoints."""

from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.common import ErrorDetail, ErrorResponse, PaginatedResponse, TagRef
from app.schemas.paper import (
    AuthorRef,
    CategoryRef,
    PaperDetail,
    PaperSummary,
    PaperTagResponse,
    PaperTagUpdate,
    PaperVersionRef,
)
from app.services.paper_service import get_paper_detail, list_papers, set_paper_tags

router = APIRouter(prefix="/api/v1/papers", tags=["papers"])


def _paper_to_summary(paper) -> PaperSummary:
    """Convert ORM Paper to PaperSummary schema."""
    categories = []
    for pc in paper.categories:
        if pc.category:
            categories.append(CategoryRef(
                id=pc.category.id,
                name=pc.category.name,
                source=pc.category.source,
            ))

    tags = []
    for pt in paper.tags:
        if pt.tag:
            tags.append(TagRef(
                id=pt.tag.id,
                name=pt.tag.name,
                color=pt.tag.color,
            ))

    author_names = []
    for pa in sorted(paper.authors, key=lambda x: x.author_order):
        if pa.author:
            author_names.append(pa.author.name)

    return PaperSummary(
        id=paper.id,
        title=paper.title,
        source=paper.source,
        source_id=paper.source_id,
        venue=paper.venue,
        published_date=paper.published_date,
        url=paper.url,
        pdf_url=paper.pdf_url,
        code_url=paper.code_url,
        crawled_at=paper.crawled_at,
        updated_at=paper.updated_at,
        categories=categories,
        tags=tags,
        author_names=author_names,
        summary_cn=paper.summary_cn,
        summary_en=paper.summary_en,
    )


def _paper_to_detail(paper) -> PaperDetail:
    """Convert ORM Paper to PaperDetail schema."""
    summary = _paper_to_summary(paper)

    authors = []
    for pa in sorted(paper.authors, key=lambda x: x.author_order):
        if pa.author:
            authors.append(AuthorRef(
                id=pa.author.id,
                name=pa.author.name,
                affiliation=pa.author.affiliation,
                author_order=pa.author_order,
            ))

    versions = []
    for v in paper.versions:
        versions.append(PaperVersionRef(
            id=v.id,
            title=v.title,
            source=v.source,
            url=v.url,
        ))

    return PaperDetail(
        **summary.model_dump(),
        abstract=paper.abstract,
        authors=authors,
        merged_into_id=paper.merged_into_id,
        versions=versions,
    )


@router.get("", response_model=PaginatedResponse[PaperSummary])
async def list_papers_endpoint(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    source: Optional[list[str]] = Query(None),
    category: Optional[list[str]] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    q: Optional[str] = Query(None),
    tag_id: Optional[list[str]] = Query(None),
    sort: str = Query("-published_date"),
    venue: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List papers with filters, search, and pagination."""
    papers, total = await list_papers(
        db,
        page=page,
        page_size=page_size,
        source=source,
        category=category,
        date_from=date_from,
        date_to=date_to,
        q=q,
        tag_id=tag_id,
        sort=sort,
        venue=venue,
    )

    items = [_paper_to_summary(p) for p in papers]
    pages = max(1, (total + page_size - 1) // page_size)

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/{paper_id}", response_model=PaperDetail, responses={404: {"model": ErrorResponse}})
async def get_paper_endpoint(
    paper_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a single paper with full detail."""
    paper = await get_paper_detail(db, paper_id)
    if paper is None:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "RESOURCE_NOT_FOUND", "message": f"Paper with id {paper_id} not found", "details": {}}},
        )

    return _paper_to_detail(paper)


@router.put("/{paper_id}/tags", response_model=PaperTagResponse, responses={404: {"model": ErrorResponse}, 422: {"model": ErrorResponse}})
async def put_paper_tags_endpoint(
    paper_id: str,
    body: PaperTagUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Replace tags on a paper."""
    try:
        paper = await set_paper_tags(db, paper_id, body.tag_ids)
    except ValueError as e:
        raise HTTPException(
            status_code=422,
            detail={"error": {"code": "INVALID_INPUT", "message": str(e), "details": {}}},
        )
    if paper is None:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "RESOURCE_NOT_FOUND", "message": f"Paper with id {paper_id} not found", "details": {}}},
        )

    tags = []
    for pt in paper.tags:
        if pt.tag:
            tags.append(TagRef(id=pt.tag.id, name=pt.tag.name, color=pt.tag.color))

    return PaperTagResponse(paper_id=paper_id, tags=tags)
