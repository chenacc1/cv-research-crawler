"""Shared test fixtures: async test client, SQLite in-memory database."""

from collections.abc import AsyncGenerator
from datetime import UTC, datetime

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
import app.models  # noqa: F401 — ensure all ORM models are registered on Base.metadata

TEST_DATABASE_URL = "sqlite+aiosqlite://"


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """Create a fresh in-memory SQLite engine for each test."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Provide an AsyncSession backed by the test engine."""
    session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Provide an async HTTP test client with DB override."""

    from app.main import app

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def seeded_categories(db_session: AsyncSession):
    """Seed some test categories."""
    from app.models.category import Category

    cats = [
        Category(id="cat-1", name="Object Detection", source="arxiv"),
        Category(id="cat-2", name="Image Segmentation", source="arxiv"),
        Category(id="cat-3", name="Generative Models", source="arxiv"),
    ]
    for c in cats:
        db_session.add(c)
    await db_session.flush()
    return cats


@pytest_asyncio.fixture
async def seeded_papers(db_session: AsyncSession, seeded_categories):
    """Seed some test papers."""
    from app.models.category import PaperCategory
    from app.models.paper import Paper

    papers = [
        Paper(
            id="paper-1",
            title="A Novel Object Detection Method",
            title_normalized="a novel object detection method",
            source="arxiv",
            source_id="2401.00001",
            url="https://arxiv.org/abs/2401.00001",
            published_date=datetime(2024, 1, 15).date(),
            crawled_at=datetime(2024, 1, 16, tzinfo=UTC),
        ),
        Paper(
            id="paper-2",
            title="Advances in Image Segmentation",
            title_normalized="advances in image segmentation",
            source="arxiv",
            source_id="2401.00002",
            url="https://arxiv.org/abs/2401.00002",
            published_date=datetime(2024, 1, 16).date(),
            crawled_at=datetime(2024, 1, 17, tzinfo=UTC),
        ),
        Paper(
            id="paper-3",
            title="A Novel Object Detection Technique",
            title_normalized="a novel object detection technique",
            source="github",
            source_id="repo-1",
            url="https://github.com/user/repo1",
            published_date=datetime(2024, 1, 17).date(),
            crawled_at=datetime(2024, 1, 18, tzinfo=UTC),
        ),
    ]
    for p in papers:
        db_session.add(p)
    await db_session.flush()

    # Link papers to categories
    links = [
        PaperCategory(paper_id="paper-1", category_id="cat-1"),
        PaperCategory(paper_id="paper-2", category_id="cat-2"),
        PaperCategory(paper_id="paper-3", category_id="cat-1"),
    ]
    for l in links:
        db_session.add(l)
    await db_session.flush()

    return papers


@pytest_asyncio.fixture
async def seeded_repos(db_session: AsyncSession):
    """Seed some test repos."""
    from app.models.repo import GitHubRepo

    repos = [
        GitHubRepo(
            id="repo-1",
            full_name="test/detection-lib",
            description="A detection library",
            url="https://github.com/test/detection-lib",
            stars=1500,
            previous_stars=1200,
            forks=300,
            language="Python",
            topics=["computer-vision", "object-detection"],
            crawled_at=datetime(2024, 1, 16, tzinfo=UTC),
        ),
        GitHubRepo(
            id="repo-2",
            full_name="test/segmentation-tool",
            description="A segmentation tool",
            url="https://github.com/test/segmentation-tool",
            stars=800,
            previous_stars=600,
            forks=150,
            language="Python",
            topics=["image-segmentation"],
            crawled_at=datetime(2024, 1, 17, tzinfo=UTC),
        ),
    ]
    for r in repos:
        db_session.add(r)
    await db_session.flush()
    return repos


@pytest_asyncio.fixture
async def seeded_tags(db_session: AsyncSession):
    """Seed some test tags."""
    from app.models.tag import UserTag

    tags = [
        UserTag(id="tag-1", name="Important", color="#EF4444"),
        UserTag(id="tag-2", name="To Read", color="#3B82F6"),
    ]
    for t in tags:
        db_session.add(t)
    await db_session.flush()
    return tags
