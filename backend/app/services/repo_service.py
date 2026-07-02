"""Repository business logic."""

from datetime import UTC, datetime

from sqlalchemy import and_, delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.repo import GitHubRepo
from app.models.tag import RepoTag, UserTag


async def list_repos(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    language: list[str] | None = None,
    topic: list[str] | None = None,
    stars_min: int | None = None,
    stars_max: int | None = None,
    pushed_after: datetime | None = None,
    pushed_before: datetime | None = None,
    tag_id: list[str] | None = None,
    q: str | None = None,
    sort: str = "-stars",
) -> tuple[list[GitHubRepo], int]:
    """List repos with filters and pagination."""
    conditions = []

    if language:
        conditions.append(GitHubRepo.language.in_(language))
    if stars_min is not None:
        conditions.append(GitHubRepo.stars >= stars_min)
    if stars_max is not None:
        conditions.append(GitHubRepo.stars <= stars_max)
    if pushed_after:
        conditions.append(GitHubRepo.pushed_at >= pushed_after)
    if pushed_before:
        conditions.append(GitHubRepo.pushed_at <= pushed_before)
    if q:
        conditions.append(
            or_(
                GitHubRepo.full_name.ilike(f"%{q}%"),
                GitHubRepo.description.ilike(f"%{q}%"),
            )
        )

    base_query = select(GitHubRepo).outerjoin(GitHubRepo.tags)

    if topic:
        # For JSON topics, use SQLite JSON functions
        topic_conditions = []
        for t in topic:
            topic_conditions.append(
                func.json_extract(GitHubRepo.topics, "$").like(f'%"{t}"%')
            )
        conditions.append(or_(*topic_conditions))

    if tag_id:
        conditions.append(RepoTag.tag_id.in_(tag_id))
        base_query = base_query.join(RepoTag).join(UserTag)

    if conditions:
        base_query = base_query.where(and_(*conditions))

    base_query = base_query.distinct()

    # Count
    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Sorting
    sort_mapping = {
        "stars": GitHubRepo.stars.desc(),
        "-stars": GitHubRepo.stars.desc(),
        "forks": GitHubRepo.forks.desc(),
        "-forks": GitHubRepo.forks.desc(),
        "pushed_at": GitHubRepo.pushed_at.asc(),
        "-pushed_at": GitHubRepo.pushed_at.desc(),
        "crawled_at": GitHubRepo.crawled_at.asc(),
        "-crawled_at": GitHubRepo.crawled_at.desc(),
    }
    order_by = sort_mapping.get(sort, GitHubRepo.stars.desc())

    base_query = base_query.options(
        selectinload(GitHubRepo.tags).joinedload(RepoTag.tag),
    )

    base_query = base_query.order_by(order_by)
    base_query = base_query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(base_query)
    repos = result.unique().scalars().all()

    return list(repos), total


async def get_repo_detail(db: AsyncSession, repo_id: str) -> GitHubRepo | None:
    """Get a single repo with tags loaded."""
    result = await db.execute(
        select(GitHubRepo)
        .where(GitHubRepo.id == repo_id)
        .options(
            selectinload(GitHubRepo.tags).joinedload(RepoTag.tag),
        )
    )
    return result.unique().scalar_one_or_none()


async def set_repo_tags(db: AsyncSession, repo_id: str, tag_ids: list[str]) -> GitHubRepo | None:
    """Replace all tags on a repo.

    Returns:
        The updated GitHubRepo, or None if the repo was not found.

    Raises:
        ValueError: if one or more tag_ids do not exist in user_tag.
    """
    repo = await get_repo_detail(db, repo_id)
    if repo is None:
        return None

    await db.execute(delete(RepoTag).where(RepoTag.repo_id == repo_id))

    if tag_ids:
        result = await db.execute(select(UserTag).where(UserTag.id.in_(tag_ids)))
        found_tags = result.scalars().all()
        missing_ids = set(tag_ids) - {t.id for t in found_tags}
        if missing_ids:
            raise ValueError(f"Invalid tag IDs: {', '.join(sorted(missing_ids))}")

        for tag_id in tag_ids:
            db.add(RepoTag(repo_id=repo_id, tag_id=tag_id))

    await db.flush()
    # Expire cached Repo so re-query fetches fresh tags
    db.expire_all()
    result = await db.execute(
        select(GitHubRepo)
        .where(GitHubRepo.id == repo_id)
        .options(
            selectinload(GitHubRepo.tags).joinedload(RepoTag.tag),
        )
    )
    return result.unique().scalar_one_or_none()


async def upsert_repo(db: AsyncSession, repo_data: dict) -> tuple[GitHubRepo, bool]:
    """Upsert a repo by full_name. Returns (repo, is_new)."""
    result = await db.execute(
        select(GitHubRepo).where(GitHubRepo.full_name == repo_data["full_name"])
    )
    existing = result.scalar_one_or_none()
    is_new = existing is None

    if existing:
        # Store current stars as previous_stars before updating
        existing.previous_stars = existing.stars
        for key, value in repo_data.items():
            if key not in ("full_name", "crawled_at") and hasattr(existing, key):
                setattr(existing, key, value)
        existing.last_crawled_at = repo_data.get("last_crawled_at", datetime.now(UTC))
        repo = existing
    else:
        repo = GitHubRepo(**repo_data)
        db.add(repo)
        await db.flush()

    return repo, is_new
