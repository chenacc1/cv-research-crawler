"""Tag business logic."""

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.tag import PaperTag, RepoTag, UserTag

TAG_COLOR_PALETTE = {
    "#EF4444", "#F97316", "#F59E0B", "#EAB308",
    "#84CC16", "#22C55E", "#10B981", "#14B8A6",
    "#06B6D4", "#3B82F6", "#6366F1", "#8B5CF6",
    "#A855F7", "#D946EF", "#EC4899", "#6B7280",
}


def is_valid_color(color: str) -> bool:
    return color in TAG_COLOR_PALETTE


async def list_tags(db: AsyncSession) -> list[dict]:
    """List all tags with paper_count and repo_count."""
    result = await db.execute(
        select(UserTag).options(
            selectinload(UserTag.papers),
            selectinload(UserTag.repos),
        ).order_by(UserTag.name)
    )
    tags = result.unique().scalars().all()

    return [
        {
            "id": t.id,
            "name": t.name,
            "color": t.color,
            "paper_count": len(t.papers),
            "repo_count": len(t.repos),
            "created_at": t.created_at,
        }
        for t in tags
    ]


async def create_tag(db: AsyncSession, name: str, color: str) -> UserTag:
    """Create a new tag."""
    tag = UserTag(name=name, color=color)
    db.add(tag)
    await db.flush()
    return tag


async def get_tag(db: AsyncSession, tag_id: str) -> UserTag | None:
    """Get a single tag."""
    result = await db.execute(select(UserTag).where(UserTag.id == tag_id))
    return result.scalar_one_or_none()


async def get_tag_by_name(db: AsyncSession, name: str) -> UserTag | None:
    """Find tag by name (for uniqueness check)."""
    result = await db.execute(select(UserTag).where(UserTag.name == name))
    return result.scalar_one_or_none()


async def update_tag(db: AsyncSession, tag_id: str, name: str | None = None, color: str | None = None) -> UserTag | None:
    """Update a tag's name and/or color."""
    tag = await get_tag(db, tag_id)
    if tag is None:
        return None
    if name is not None:
        tag.name = name
    if color is not None:
        tag.color = color
    await db.flush()
    return tag


async def delete_tag(db: AsyncSession, tag_id: str) -> bool:
    """Delete a tag and its associations."""
    tag = await get_tag(db, tag_id)
    if tag is None:
        return False
    # Cascading deletes handle paper_tag and repo_tag via FK ondelete CASCADE
    await db.delete(tag)
    await db.flush()
    return True
