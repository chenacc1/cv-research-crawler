"""Crawl keyword filtering — only ingest items matching configured interests."""

from app.config import settings


def parse_keywords(config_value: str) -> list[str]:
    """Parse comma-separated keyword string into a trimmed, lowercased list."""
    if not config_value or not config_value.strip():
        return []
    return [kw.strip().lower() for kw in config_value.split(",") if kw.strip()]


async def get_active_keywords(db) -> list[str]:
    """Get enabled keywords from database. Falls back to config if DB is empty."""
    from app.services.crawl_keyword_service import get_enabled_keywords_str
    kw = await get_enabled_keywords_str(db)
    if not kw:
        # Fall back to config keywords
        kw = parse_keywords(settings.crawler_keywords)
    return kw


def matches_keywords(text_parts: list[str], keywords: list[str]) -> bool:
    """Check if any keyword matches any text part (case-insensitive substring).
    Returns True if keywords is empty (no filtering applied).
    """
    if not keywords:
        return True
    combined = " ".join(text_parts).lower()
    return any(kw in combined for kw in keywords)
