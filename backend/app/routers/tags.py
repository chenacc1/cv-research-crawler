"""Tags API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.tag import PaperTag, RepoTag, UserTag
from app.schemas.common import ErrorResponse
from app.schemas.tag import TagCreate, TagDetail, TagListResponse, TagUpdate
from app.services.tag_service import (
    create_tag,
    delete_tag,
    get_tag,
    get_tag_by_name,
    is_valid_color,
    list_tags,
    update_tag,
)

router = APIRouter(prefix="/api/v1/tags", tags=["tags"])


@router.get("", response_model=TagListResponse)
async def list_tags_endpoint(
    db: AsyncSession = Depends(get_db),
):
    """List all user-defined tags."""
    tags = await list_tags(db)
    return TagListResponse(items=[TagDetail(**t) for t in tags])


@router.post(
    "",
    response_model=TagDetail,
    status_code=201,
    responses={409: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
async def create_tag_endpoint(
    body: TagCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new tag."""
    # Validate color
    if not is_valid_color(body.color):
        raise HTTPException(
            status_code=422,
            detail={"error": {"code": "VALIDATION_ERROR", "message": f"Color '{body.color}' is not in the allowed palette", "details": {}}},
        )

    # Check name uniqueness
    existing = await get_tag_by_name(db, body.name)
    if existing:
        raise HTTPException(
            status_code=409,
            detail={"error": {"code": "RESOURCE_CONFLICT", "message": f"Tag name '{body.name}' already exists", "details": {}}},
        )

    tag = await create_tag(db, body.name, body.color)
    return TagDetail(
        id=tag.id,
        name=tag.name,
        color=tag.color,
        paper_count=0,
        repo_count=0,
        created_at=tag.created_at,
    )


@router.put(
    "/{tag_id}",
    response_model=TagDetail,
    responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
async def update_tag_endpoint(
    tag_id: str,
    body: TagUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a tag's name and/or color."""
    # Check existence
    existing = await get_tag(db, tag_id)
    if existing is None:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "RESOURCE_NOT_FOUND", "message": f"Tag with id {tag_id} not found", "details": {}}},
        )

    # Validate color if provided
    if body.color is not None and not is_valid_color(body.color):
        raise HTTPException(
            status_code=422,
            detail={"error": {"code": "VALIDATION_ERROR", "message": f"Color '{body.color}' is not in the allowed palette", "details": {}}},
        )

    # Check name uniqueness if name is being changed
    if body.name is not None:
        existing_name = await get_tag_by_name(db, body.name)
        if existing_name and existing_name.id != tag_id:
            raise HTTPException(
                status_code=409,
                detail={"error": {"code": "RESOURCE_CONFLICT", "message": f"Tag name '{body.name}' already exists", "details": {}}},
            )

    tag = await update_tag(db, tag_id, body.name, body.color)
    if tag is None:
        raise HTTPException(status_code=404, detail="Tag not found")

    # Get counts using proper SQLAlchemy queries
    paper_count_result = await db.execute(
        select(func.count(PaperTag.paper_id)).where(PaperTag.tag_id == tag_id)
    )
    paper_count = paper_count_result.scalar() or 0

    repo_count_result = await db.execute(
        select(func.count(RepoTag.repo_id)).where(RepoTag.tag_id == tag_id)
    )
    repo_count = repo_count_result.scalar() or 0

    return TagDetail(
        id=tag.id,
        name=tag.name,
        color=tag.color,
        paper_count=paper_count,
        repo_count=repo_count,
        created_at=tag.created_at,
    )


@router.delete(
    "/{tag_id}",
    status_code=204,
    responses={404: {"model": ErrorResponse}},
)
async def delete_tag_endpoint(
    tag_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a tag."""
    success = await delete_tag(db, tag_id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "RESOURCE_NOT_FOUND", "message": f"Tag with id {tag_id} not found", "details": {}}},
        )
    return None
