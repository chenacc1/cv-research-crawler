"""FastAPI application factory with lifespan, middleware, and all routers."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import async_session_factory, engine, Base

logger = logging.getLogger(__name__)


async def _setup_sqlite_pragmas() -> None:
    """Enable SQLite WAL mode and other pragmas."""
    if "sqlite" not in settings.database_url:
        return

    async with engine.begin() as conn:
        await conn.exec_driver_sql("PRAGMA journal_mode=WAL")
        await conn.exec_driver_sql("PRAGMA foreign_keys=ON")


async def _setup_fts5() -> None:
    """Create SQLite FTS5 virtual table and triggers.

    Uses a standalone FTS5 table (no content= / content_rowid=) because
    Paper.id is a UUID string, not an INTEGER as content_rowid requires.
    The paper_id column stores the UUID for joins.  FTS5 supports regular
    DELETE statements, so triggers use DELETE ... WHERE paper_id = ... to
    keep the index in sync without needing a deterministic integer rowid.
    """
    if "sqlite" not in settings.database_url:
        return

    async with engine.begin() as conn:
        # Create standalone FTS5 virtual table.
        # paper_id is UNINDEXED (it's a join key, not searchable text).
        await conn.exec_driver_sql("""
            CREATE VIRTUAL TABLE IF NOT EXISTS paper_fts USING fts5(
                paper_id UNINDEXED,
                title,
                abstract
            );
        """)

        # Triggers to keep FTS in sync.
        # INSERT: add a row when a paper is inserted.
        await conn.exec_driver_sql("""
            CREATE TRIGGER IF NOT EXISTS paper_ai AFTER INSERT ON paper BEGIN
                INSERT INTO paper_fts(paper_id, title, abstract)
                VALUES (new.id, new.title, new.abstract);
            END;
        """)

        # DELETE: remove the FTS row when a paper is deleted.
        await conn.exec_driver_sql("""
            CREATE TRIGGER IF NOT EXISTS paper_ad AFTER DELETE ON paper BEGIN
                DELETE FROM paper_fts WHERE paper_id = old.id;
            END;
        """)

        # UPDATE: replace the old FTS row with the new values.
        await conn.exec_driver_sql("""
            CREATE TRIGGER IF NOT EXISTS paper_au AFTER UPDATE ON paper BEGIN
                DELETE FROM paper_fts WHERE paper_id = old.id;
                INSERT INTO paper_fts(paper_id, title, abstract)
                VALUES (new.id, new.title, new.abstract);
            END;
        """)


async def _setup_migrations() -> None:
    """Apply schema migrations safely (idempotent via try/except).

    Adds any new columns that may be missing from existing databases.
    Each ALTER is wrapped so a column that already exists is a no-op.
    """
    if "sqlite" not in settings.database_url:
        return

    migrations = [
        ("paper", "summary_cn", "TEXT"),
        ("paper", "summary_en", "TEXT"),
        ("github_repo", "summary_cn", "TEXT"),
        ("github_repo", "summary_en", "TEXT"),
        ("crawl_keyword", "keyword", "VARCHAR(128)"),
        ("crawl_keyword", "enabled", "BOOLEAN DEFAULT 1"),
        ("crawl_keyword", "created_at", "DATETIME"),
        ("crawl_log", "items_filtered", "INTEGER DEFAULT 0"),
        ("crawl_log", "items_summarized", "INTEGER DEFAULT 0"),
    ]

    async with engine.begin() as conn:
        for table, column, col_type in migrations:
            try:
                await conn.exec_driver_sql(
                    f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"
                )
                logger.info(f"Migration: added {table}.{column}")
            except Exception:
                logger.debug(f"Migration: {table}.{column} already exists, skipping")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: startup and shutdown."""
    # --- Startup ---
    # Apply log level from settings before any other logging
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    )
    logger.info("Starting application...")

    # Ensure data directory exists for SQLite
    data_dir = Path("./data")
    data_dir.mkdir(parents=True, exist_ok=True)

    # Ensure reports directory exists
    reports_dir = Path(settings.report_output_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)

    # Enable SQLite optimizations
    await _setup_sqlite_pragmas()

    # Create tables and FTS5
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await _setup_fts5()

    # Apply schema migrations for new columns (idempotent)
    await _setup_migrations()

    # Import crawlers to register them
    import app.crawlers  # noqa: F401

    # Start scheduler
    from app.engine.scheduler import setup_scheduler
    setup_scheduler()
    logger.info("Application startup complete")

    yield

    # --- Shutdown ---
    from app.engine.scheduler import scheduler
    scheduler.shutdown(wait=False)
    await engine.dispose()
    logger.info("Application shut down")


app = FastAPI(
    title="CV Research Paper Crawler",
    description="Knowledge crawler for CV research papers and GitHub repositories",
    version=settings.app_version,
    lifespan=lifespan,
)

# CORS
origins = [origin.strip() for origin in settings.api_cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    import uuid
    request_id = str(uuid.uuid4())
    response = await call_next(request)
    response.headers["X-Request-Id"] = request_id
    return response


# Global exception handler
@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    logger.exception("Internal server error")
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "details": {},
            }
        },
    )


# Include all routers
from app.routers import papers, repos, tags, reports, crawls, categories, authors, crawl_keywords

app.include_router(papers.router)
app.include_router(repos.router)
app.include_router(tags.router)
app.include_router(reports.router)
app.include_router(crawls.router)
app.include_router(categories.router)
app.include_router(authors.router)
app.include_router(crawl_keywords.router)


# --- System Routes ---

@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint."""
    from app.engine.scheduler import scheduler

    db_status = "disconnected"
    try:
        async with async_session_factory() as session:
            from sqlalchemy import text
            await session.execute(text("SELECT 1"))
            db_status = "connected"
    except Exception:
        db_status = "disconnected"

    scheduler_status = "running" if scheduler.running else "stopped"

    return {
        "status": "ok" if db_status == "connected" else "degraded",
        "timestamp": datetime.now(UTC),
        "database": db_status,
        "scheduler": scheduler_status,
        "version": settings.app_version,
    }


@app.get("/api/v1/stats")
async def get_stats():
    """Dashboard statistics endpoint."""
    from app.services.crawl_service import get_stats

    async with async_session_factory() as db:
        stats = await get_stats(db)

    return stats


# Run with: uvicorn app.main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
