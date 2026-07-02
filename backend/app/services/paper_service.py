"""Paper business logic."""

import math
import re
from datetime import date
from difflib import SequenceMatcher

from sqlalchemy import and_, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.models.author import Author, PaperAuthor
from app.models.category import Category, PaperCategory
from app.models.paper import Paper
from app.models.tag import PaperTag, UserTag


def normalize_title(title: str) -> str:
    """Lowercase, remove punctuation, collapse whitespace."""
    title = title.lower()
    title = re.sub(r"[^\w\s]", "", title)
    title = re.sub(r"\s+", " ", title).strip()
    return title


async def find_or_create_author(db: AsyncSession, name: str, affiliation: str | None = None) -> Author:
    """Find an author by name or create a new one."""
    result = await db.execute(select(Author).where(Author.name == name))
    author = result.scalar_one_or_none()
    if author is None:
        author = Author(name=name, affiliation=affiliation)
        db.add(author)
        await db.flush()
    elif affiliation and not author.affiliation:
        author.affiliation = affiliation
    return author


async def find_or_create_category(db: AsyncSession, name: str, source: str) -> Category:
    """Find a category by (source, name) or create a new one."""
    result = await db.execute(
        select(Category).where(and_(Category.source == source, Category.name == name))
    )
    category = result.scalar_one_or_none()
    if category is None:
        category = Category(name=name, source=source)
        db.add(category)
        await db.flush()
    return category


async def upsert_paper(db: AsyncSession, paper_data: dict) -> tuple[Paper, bool]:
    """Upsert a paper by (source, source_id). Returns (paper, is_new)."""
    result = await db.execute(
        select(Paper).where(
            and_(Paper.source == paper_data["source"], Paper.source_id == paper_data["source_id"])
        )
    )
    existing = result.scalar_one_or_none()
    is_new = existing is None

    if existing:
        # Update existing paper
        for key, value in paper_data.items():
            if key not in ("source", "source_id", "title_normalized") and hasattr(existing, key):
                setattr(existing, key, value)
        paper = existing
    else:
        paper = Paper(**paper_data)
        db.add(paper)
        await db.flush()

    return paper, is_new


async def dedup_by_title(db: AsyncSession, paper: Paper) -> None:
    """Check title similarity against papers from other sources; merge if similar."""
    if paper.merged_into_id is not None:
        return  # Already merged

    # Find papers from other sources with similar normalized titles
    result = await db.execute(
        select(Paper).where(
            and_(
                Paper.source != paper.source,
                Paper.id != paper.id,
                Paper.merged_into_id.is_(None),
            )
        )
    )
    candidates = result.scalars().all()

    for candidate in candidates:
        ratio = SequenceMatcher(None, paper.title_normalized, candidate.title_normalized).ratio()
        if ratio >= 0.85:
            # Point the newer paper to the older one
            if paper.crawled_at < candidate.crawled_at:
                candidate.merged_into_id = paper.id
            else:
                paper.merged_into_id = candidate.id
            await db.flush()
            break


async def get_paper_fts_query(query: str):
    """Build FTS5 query for papers."""
    # Escape special FTS5 characters and quote the query
    safe_query = query.replace('"', '""').strip()
    return text(
        "SELECT paper.id FROM paper "
        "JOIN paper_fts ON paper.id = paper_fts.paper_id "
        "WHERE paper_fts MATCH :query"
    ).bindparams(query=f'"{safe_query}"')


async def list_papers(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    source: list[str] | None = None,
    category: list[str] | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    q: str | None = None,
    tag_id: list[str] | None = None,
    sort: str = "-published_date",
    venue: str | None = None,
) -> tuple[list[Paper], int]:
    """List papers with filters, search, and pagination."""
    conditions = [Paper.merged_into_id.is_(None)]  # Only canonical records

    if source:
        conditions.append(Paper.source.in_(source))
    if date_from:
        conditions.append(Paper.published_date >= date_from)
    if date_to:
        conditions.append(Paper.published_date <= date_to)
    if venue:
        conditions.append(Paper.venue.ilike(f"%{venue}%"))

    base_query = select(Paper).outerjoin(Paper.categories).outerjoin(Paper.tags)

    if category:
        base_query = base_query.join(PaperCategory).join(Category).where(
            Category.name.in_(category)
        )
    if tag_id:
        base_query = base_query.join(PaperTag).join(UserTag).where(
            UserTag.id.in_(tag_id)
        )

    if q:
        fts_query = await get_paper_fts_query(q)
        conditions.append(Paper.id.in_(fts_query))

    if conditions:
        base_query = base_query.where(and_(*conditions))

    # Get total count
    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Sorting
    sort_mapping = {
        "published_date": Paper.published_date.asc(),
        "-published_date": Paper.published_date.desc(),
        "crawled_at": Paper.crawled_at.asc(),
        "-crawled_at": Paper.crawled_at.desc(),
        "title": Paper.title.asc(),
        "-title": Paper.title.desc(),
    }
    order_by = sort_mapping.get(sort, Paper.published_date.desc())

    # Apply selectinload for relationships
    base_query = base_query.options(
        selectinload(Paper.authors).joinedload(PaperAuthor.author),
        selectinload(Paper.categories).joinedload(PaperCategory.category),
        selectinload(Paper.tags).joinedload(PaperTag.tag),
    )

    base_query = base_query.order_by(order_by).distinct()
    base_query = base_query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(base_query)
    papers = result.unique().scalars().all()

    return list(papers), total


async def get_paper_detail(db: AsyncSession, paper_id: str) -> Paper | None:
    """Get a single paper with all relationships loaded."""
    result = await db.execute(
        select(Paper)
        .where(Paper.id == paper_id)
        .options(
            selectinload(Paper.authors).joinedload(PaperAuthor.author),
            selectinload(Paper.categories).joinedload(PaperCategory.category),
            selectinload(Paper.tags).joinedload(PaperTag.tag),
            selectinload(Paper.versions),
        )
    )
    return result.unique().scalar_one_or_none()


async def set_paper_tags(db: AsyncSession, paper_id: str, tag_ids: list[str]) -> Paper | None:
    """Replace all tags on a paper with the given set.

    Returns:
        The updated Paper, or None if the paper was not found.

    Raises:
        ValueError: if one or more tag_ids do not exist in user_tag.
    """
    paper = await get_paper_detail(db, paper_id)
    if paper is None:
        return None

    # Clear existing tags
    from sqlalchemy import delete as sa_delete
    await db.execute(sa_delete(PaperTag).where(PaperTag.paper_id == paper_id))

    # Verify all tags exist
    if tag_ids:
        result = await db.execute(select(UserTag).where(UserTag.id.in_(tag_ids)))
        found_tags = result.scalars().all()
        missing_ids = set(tag_ids) - {t.id for t in found_tags}
        if missing_ids:
            raise ValueError(f"Invalid tag IDs: {', '.join(sorted(missing_ids))}")

        for tag_id in tag_ids:
            db.add(PaperTag(paper_id=paper_id, tag_id=tag_id))

    await db.flush()
    # Expire cached Paper so re-query fetches fresh tags
    db.expire_all()
    result = await db.execute(
        select(Paper)
        .where(Paper.id == paper_id)
        .options(
            selectinload(Paper.authors).joinedload(PaperAuthor.author),
            selectinload(Paper.categories).joinedload(PaperCategory.category),
            selectinload(Paper.tags).joinedload(PaperTag.tag),
            selectinload(Paper.versions),
        )
    )
    return result.unique().scalar_one_or_none()
