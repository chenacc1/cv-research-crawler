"""Repository API endpoints."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.common import ErrorResponse, PaginatedResponse, TagRef
from app.schemas.repo import (
    RepoDetail,
    RepoSummary,
    RepoTagResponse,
    RepoTagUpdate,
)
from app.services.repo_service import get_repo_detail, list_repos, set_repo_tags

router = APIRouter(prefix="/api/v1/repos", tags=["repos"])


def _repo_to_summary(repo) -> RepoSummary:
    """Convert ORM GitHubRepo to RepoSummary schema."""
    tags = []
    for rt in repo.tags:
        if rt.tag:
            tags.append(TagRef(
                id=rt.tag.id,
                name=rt.tag.name,
                color=rt.tag.color,
            ))

    return RepoSummary(
        id=repo.id,
        full_name=repo.full_name,
        description=repo.description,
        url=repo.url,
        stars=repo.stars,
        forks=repo.forks,
        language=repo.language,
        topics=repo.topics or [],
        pushed_at=repo.pushed_at,
        crawled_at=repo.crawled_at,
        last_crawled_at=repo.last_crawled_at,
        tags=tags,
        summary_cn=repo.summary_cn,
        summary_en=repo.summary_en,
    )


def _repo_to_detail(repo) -> RepoDetail:
    """Convert ORM GitHubRepo to RepoDetail schema."""
    summary = _repo_to_summary(repo)
    return RepoDetail(**summary.model_dump())


@router.get("", response_model=PaginatedResponse[RepoSummary])
async def list_repos_endpoint(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    language: Optional[list[str]] = Query(None),
    topic: Optional[list[str]] = Query(None),
    stars_min: Optional[int] = Query(None),
    stars_max: Optional[int] = Query(None),
    pushed_after: Optional[datetime] = Query(None),
    pushed_before: Optional[datetime] = Query(None),
    tag_id: Optional[list[str]] = Query(None),
    q: Optional[str] = Query(None),
    sort: str = Query("-stars"),
    db: AsyncSession = Depends(get_db),
):
    """List repos with filters and pagination."""
    repos, total = await list_repos(
        db,
        page=page,
        page_size=page_size,
        language=language,
        topic=topic,
        stars_min=stars_min,
        stars_max=stars_max,
        pushed_after=pushed_after,
        pushed_before=pushed_before,
        tag_id=tag_id,
        q=q,
        sort=sort,
    )

    items = [_repo_to_summary(r) for r in repos]
    pages = max(1, (total + page_size - 1) // page_size)

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/{repo_id}", response_model=RepoDetail, responses={404: {"model": ErrorResponse}})
async def get_repo_endpoint(
    repo_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a single repo with detail."""
    repo = await get_repo_detail(db, repo_id)
    if repo is None:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "RESOURCE_NOT_FOUND", "message": f"Repo with id {repo_id} not found", "details": {}}},
        )

    return _repo_to_detail(repo)


@router.put("/{repo_id}/tags", response_model=RepoTagResponse, responses={404: {"model": ErrorResponse}, 422: {"model": ErrorResponse}})
async def put_repo_tags_endpoint(
    repo_id: str,
    body: RepoTagUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Replace tags on a repo."""
    try:
        repo = await set_repo_tags(db, repo_id, body.tag_ids)
    except ValueError as e:
        raise HTTPException(
            status_code=422,
            detail={"error": {"code": "INVALID_INPUT", "message": str(e), "details": {}}},
        )
    if repo is None:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "RESOURCE_NOT_FOUND", "message": f"Repo with id {repo_id} not found", "details": {}}},
        )

    tags = []
    for rt in repo.tags:
        if rt.tag:
            tags.append(TagRef(id=rt.tag.id, name=rt.tag.name, color=rt.tag.color))

    return RepoTagResponse(repo_id=repo_id, tags=tags)
