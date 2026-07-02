"""CrawlKeyword business logic."""

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.keyword import CrawlKeyword


async def get_all_keywords(db: AsyncSession) -> list[CrawlKeyword]:
    result = await db.execute(
        select(CrawlKeyword).order_by(CrawlKeyword.created_at.desc())
    )
    return list(result.scalars().all())


async def get_enabled_keywords_str(db: AsyncSession) -> list[str]:
    result = await db.execute(
        select(CrawlKeyword.keyword).where(CrawlKeyword.enabled == True)
    )
    return [row[0] for row in result.all()]


async def add_keywords(db: AsyncSession, keywords: list[str]) -> list[CrawlKeyword]:
    """Add new keywords (duplicates skipped). Returns all current keywords."""
    existing = set()
    result = await db.execute(select(CrawlKeyword.keyword))
    for row in result.all():
        existing.add(row[0])

    added = []
    for kw in keywords:
        kw = kw.strip().lower()
        if kw and kw not in existing:
            k = CrawlKeyword(keyword=kw, enabled=True)
            db.add(k)
            added.append(k)
            existing.add(kw)

    await db.flush()
    return added


async def set_keywords(db: AsyncSession, keywords: list[str]) -> list[CrawlKeyword]:
    """Replace all keywords with a new set (all enabled)."""
    await db.execute(delete(CrawlKeyword))
    await db.flush()
    return await add_keywords(db, keywords)


async def toggle_keyword(db: AsyncSession, kw_id: str, enabled: bool) -> CrawlKeyword | None:
    result = await db.execute(select(CrawlKeyword).where(CrawlKeyword.id == kw_id))
    kw = result.scalar_one_or_none()
    if kw:
        kw.enabled = enabled
        await db.flush()
    return kw


async def delete_keyword(db: AsyncSession, kw_id: str) -> bool:
    result = await db.execute(select(CrawlKeyword).where(CrawlKeyword.id == kw_id))
    kw = result.scalar_one_or_none()
    if kw:
        await db.delete(kw)
        await db.flush()
        return True
    return False
