# Architecture Document — Paper + GitHub Knowledge Crawler

**Author:** Architect  
**Date:** 2026-06-29  
**Status:** Draft  

---

## 1. Tech Stack

### 1.1 Overview

| Layer | Choice | Version | Rationale |
|-------|--------|---------|-----------|
| **Language** | Python | 3.12+ | Excellent ecosystem for crawling (httpx, BeautifulSoup), ORM (SQLAlchemy), and async (FastAPI). Wide library support for academic data formats. |
| **Web framework** | FastAPI | 0.115+ | Native async, automatic OpenAPI schema, Pydantic validation, high performance. Perfect fit for an API-centric monolith that does background crawling. |
| **ORM** | SQLAlchemy | 2.0+ | Mature, supports both SQLite and PostgreSQL with identical query syntax. Declarative models with relationship loading. Alembic integration. |
| **Schema validation** | Pydantic | 2.x | First-class FastAPI integration; request/response shapes are typed and validated automatically. |
| **Task scheduling** | APScheduler | 3.x | In-process cron scheduler. No external broker (Redis/RabbitMQ) required for V1 single-user deployment. Sufficient for 2-6h intervals. Swap to Celery later if horizontal scaling is needed. |
| **Migrations** | Alembic | 1.14+ | Works with both SQLite and PostgreSQL. Autogenerate from SQLAlchemy models. |
| **Frontend framework** | React | 18.x | Industry standard for interactive dashboards. Large ecosystem, strong TypeScript support. |
| **Build tool** | Vite | 6.x | Fast HMR during dev, optimized production builds with tree-shaking. Targets pure SPA (no SSR needed). |
| **Styling** | Tailwind CSS | 4.x | Utility-first, rapid prototyping, consistent design system. Keeps bundle small via purging. |
| **Type safety** | TypeScript | 5.x | Catch data-shape mismatches between frontend types and API responses at compile time. |
| **HTTP client (frontend)** | axios | 1.x | Interceptors for error handling, cleaner API than fetch for REST patterns. |
| **Markdown rendering (FE)** | react-markdown | 9.x | Render report Markdown inline; supports GFM tables and syntax highlighting via remark/rehype plugins. |
| **Markdown generation (BE)** | Jinja2 | 3.x | Templates are version-controlled files. Natural fit for generating structured Markdown with loops/conditionals. |
| **Full-text search** | SQLite FTS5 | built-in | Zero-infrastructure full-text search on title + abstract. Sufficient for single-user corpus size (10k-100k papers). PostgreSQL tsvector available as upgrade path. |
| **Containerization** | Docker Compose | v2 | Single `docker-compose up` for all components (API + frontend + optional PostgreSQL). |
| **Async HTTP (crawlers)** | httpx | 0.28+ | Async HTTP client with connection pooling, timeout control, and retry support -- used by all crawlers. |
| **Testing** | pytest + pytest-asyncio | 8.x | Standard Python test framework with async support for testing crawlers and API endpoints. |

### 1.2 Rationale for Key Decisions

**Modular monolith over microservices.** The system is single-user and local-first. A monolith keeps deployment simple (one process) while a plugin-based crawler registry provides the same extensibility benefit of microservices (new source = one file + registration) without distributed-system complexity. If multi-user support is added in P2, the API layer can be horizontally scaled behind a load balancer.

**APScheduler over Celery/RQ.** Celery requires a message broker (Redis/RabbitMQ) and worker processes. For V1's 2-6h crawl intervals and single-instance deployment, an in-process scheduler is simpler and sufficient. The scheduler is abstracted behind `engine/scheduler.py`, so swapping to Celery later only requires changing that module.

**SQLite default, PostgreSQL optional.** SQLite with WAL mode supports concurrent reads and a single writer, which matches the single-user local deployment. PostgreSQL is one connection-string change away for server deployments where concurrent write access matters.

**UUID primary keys.** Prevents ID collision if data is ever merged across instances. Slightly larger than auto-increment integers but the corpus size (10k-100k records) makes the difference negligible.

**Jinja2 for reports over DB-stored templates.** Report templates change infrequently and benefit from version control. Jinja2 files in the repo are editable with any text editor and reviewable in PRs.

---

## 2. Repository & Directory Structure

```
paper-crawler/
├── docker-compose.yml              # Single-stack orchestration
├── .env.example                    # Documented environment variables
├── README.md
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/               # Migration files
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app factory, lifespan, middleware
│   │   ├── config.py               # Pydantic BaseSettings, env loading
│   │   ├── database.py             # Engine, sessionmaker, get_db dependency
│   │   │
│   │   ├── models/                 # SQLAlchemy ORM models
│   │   │   ├── __init__.py
│   │   │   ├── paper.py            # Paper, PaperFTS (FTS5)
│   │   │   ├── author.py           # Author, PaperAuthor
│   │   │   ├── category.py         # Category, PaperCategory
│   │   │   ├── repo.py             # GitHubRepo
│   │   │   ├── tag.py              # UserTag, PaperTag, RepoTag
│   │   │   ├── crawl_log.py        # CrawlLog
│   │   │   └── report.py           # Report
│   │   │
│   │   ├── schemas/                # Pydantic request/response schemas
│   │   │   ├── __init__.py
│   │   │   ├── paper.py
│   │   │   ├── repo.py
│   │   │   ├── tag.py
│   │   │   ├── report.py
│   │   │   ├── crawl.py
│   │   │   └── common.py           # PaginatedResponse, ErrorResponse
│   │   │
│   │   ├── routers/                # API route handlers
│   │   │   ├── __init__.py
│   │   │   ├── papers.py
│   │   │   ├── repos.py
│   │   │   ├── tags.py
│   │   │   ├── reports.py
│   │   │   ├── crawls.py
│   │   │   ├── categories.py
│   │   │   └── authors.py
│   │   │
│   │   ├── crawlers/               # Crawler plugin system
│   │   │   ├── __init__.py
│   │   │   ├── base.py             # BaseCrawler ABC
│   │   │   ├── registry.py         # CrawlerRegistry
│   │   │   ├── arxiv.py            # ArxivCrawler
│   │   │   └── github.py           # GitHubCrawler
│   │   │
│   │   ├── engine/                 # Background processing
│   │   │   ├── __init__.py
│   │   │   ├── scheduler.py        # APScheduler setup, job registration
│   │   │   ├── report_generator.py # Query DB -> render Jinja2 -> save file
│   │   │   └── templates/          # Jinja2 Markdown templates
│   │   │       ├── daily.md.j2
│   │   │       └── weekly.md.j2
│   │   │
│   │   └── services/               # Business logic layer
│   │       ├── __init__.py
│   │       ├── paper_service.py
│   │       ├── repo_service.py
│   │       ├── tag_service.py
│   │       ├── report_service.py
│   │       └── crawl_service.py
│   │
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py             # Fixtures (test DB, test client)
│       ├── test_crawlers/
│       ├── test_routers/
│       └── test_services/
│
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf                  # Production nginx config (reverse proxy + static)
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   ├── index.html
│   ├── public/
│   └── src/
│       ├── main.tsx                # ReactDOM.createRoot
│       ├── App.tsx                 # React Router layout
│       ├── index.css               # Tailwind directives + global styles
│       │
│       ├── api/                    # API client layer
│       │   ├── client.ts           # axios instance, interceptors
│       │   ├── papers.ts
│       │   ├── repos.ts
│       │   ├── tags.ts
│       │   ├── reports.ts
│       │   └── crawls.ts
│       │
│       ├── types/                  # TypeScript type definitions
│       │   ├── paper.ts
│       │   ├── repo.ts
│       │   ├── tag.ts
│       │   ├── report.ts
│       │   └── common.ts           # PaginatedResponse<T>, ApiError
│       │
│       ├── hooks/                  # Custom React hooks
│       │   ├── usePapers.ts
│       │   ├── useRepos.ts
│       │   ├── useTags.ts
│       │   ├── useReports.ts
│       │   └── useDebounce.ts
│       │
│       ├── components/
│       │   ├── layout/
│       │   │   ├── AppShell.tsx     # Sidebar + main content layout
│       │   │   ├── Sidebar.tsx      # Navigation: Papers, Repos, Tags, Reports, Crawls
│       │   │   └── Header.tsx
│       │   └── shared/
│       │       ├── FilterBar.tsx    # Generic filter bar with chips
│       │       ├── FilterChip.tsx   # Removable filter indicator
│       │       ├── Pagination.tsx   # Page navigation
│       │       ├── SortableTable.tsx
│       │       ├── TagBadge.tsx     # Colored tag badge
│       │       ├── TagSelector.tsx  # Multi-tag picker
│       │       ├── DateRangePicker.tsx
│       │       ├── MarkdownViewer.tsx  # react-markdown wrapper
│       │       ├── StatusBadge.tsx  # Colored status indicator
│       │       └── LoadingSkeleton.tsx
│       │
│       └── pages/
│           ├── PaperListPage.tsx
│           ├── PaperDetailPage.tsx
│           ├── RepoListPage.tsx
│           ├── RepoDetailPage.tsx
│           ├── TagManagePage.tsx
│           ├── ReportListPage.tsx
│           ├── ReportViewPage.tsx
│           └── CrawlStatusPage.tsx
│
└── reports/                        # Generated Markdown reports (gitignored)
```

---

## 3. Data Model

### 3.1 Entity-Relationship Overview

```
Paper ──< PaperAuthor >── Author
Paper ──< PaperCategory >── Category
Paper ──< PaperTag >── UserTag
GitHubRepo ──< RepoTag >── UserTag

CrawlLog (standalone audit table)
Report   (standalone, referenced by file_path)
```

### 3.2 ORM Models

#### Paper

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | UUID | PK, default=uuid4 | |
| `title` | String(1024) | NOT NULL | Raw title from source |
| `title_normalized` | String(1024) | NOT NULL | Lowercased, whitespace-collapsed. Used for dedup merge. |
| `abstract` | Text | nullable | |
| `url` | String(2048) | NOT NULL | Canonical link to paper page |
| `pdf_url` | String(2048) | nullable | Direct PDF link |
| `code_url` | String(2048) | nullable | Associated code repository URL |
| `source` | String(32) | NOT NULL | `arxiv`, `dblp`, `openreview` |
| `source_id` | String(128) | NOT NULL | Source-specific identifier (e.g. arxiv ID `2301.12345`) |
| `venue` | String(256) | nullable | Conference/journal name |
| `published_date` | Date | nullable | Publication or submission date |
| `crawled_at` | DateTime(UTC) | NOT NULL, default=utcnow | When first ingested |
| `updated_at` | DateTime(UTC) | NOT NULL, default=utcnow, onupdate=utcnow | |

**Indexes:**
- `uq_paper_source_id` UNIQUE on `(source, source_id)` -- dedup identity
- `ix_paper_published_date` on `published_date DESC`
- `ix_paper_crawled_at` on `crawled_at`
- `ix_paper_title_normalized` on `title_normalized` -- dedup merge lookup
- `ix_paper_source` on `source` -- filter by source

**Relationships:**
- `authors` -- many-to-many via PaperAuthor
- `categories` -- many-to-many via PaperCategory
- `tags` -- many-to-many via PaperTag

#### PaperFTS (SQLite FTS5 Virtual Table)

| Column | Notes |
|--------|-------|
| `title` | Content column |
| `abstract` | Content column |

Maintained by triggers on Paper INSERT/UPDATE/DELETE. For PostgreSQL, replace with a GIN-indexed `tsvector` column on Paper.

#### Author

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | UUID | PK, default=uuid4 |
| `name` | String(256) | NOT NULL, UNIQUE |
| `affiliation` | Text | nullable |

**Indexes:**
- `uq_author_name` UNIQUE on `name`

#### PaperAuthor (join)

| Column | Type | Constraints |
|--------|------|-------------|
| `paper_id` | UUID | FK → Paper.id ON DELETE CASCADE |
| `author_id` | UUID | FK → Author.id ON DELETE CASCADE |
| `author_order` | Integer | default=0 |

**Indexes:**
- `uq_paper_author` UNIQUE on `(paper_id, author_id)`
- `ix_paper_author_author` on `author_id`

#### Category

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | UUID | PK, default=uuid4 |
| `name` | String(128) | NOT NULL |
| `source` | String(32) | NOT NULL |

**Indexes:**
- `uq_category_source_name` UNIQUE on `(source, name)`

#### PaperCategory (join)

| Column | Type | Constraints |
|--------|------|-------------|
| `paper_id` | UUID | FK → Paper.id ON DELETE CASCADE |
| `category_id` | UUID | FK → Category.id ON DELETE CASCADE |

**Indexes:**
- `uq_paper_category` UNIQUE on `(paper_id, category_id)`

#### GitHubRepo

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | UUID | PK, default=uuid4 | |
| `full_name` | String(256) | NOT NULL, UNIQUE | `owner/repo` |
| `description` | Text | nullable | |
| `url` | String(2048) | NOT NULL | `https://github.com/{full_name}` |
| `stars` | Integer | default=0 | |
| `forks` | Integer | default=0 | |
| `language` | String(64) | nullable | Primary programming language |
| `topics` | JSON | nullable | List of topic strings |
| `pushed_at` | DateTime(UTC) | nullable | Last push timestamp from GitHub |
| `crawled_at` | DateTime(UTC) | NOT NULL, default=utcnow | First seen |
| `last_crawled_at` | DateTime(UTC) | NOT NULL, default=utcnow | Last time we checked this repo |

**Indexes:**
- `uq_repo_full_name` UNIQUE on `full_name`
- `ix_repo_stars` on `stars DESC`
- `ix_repo_pushed_at` on `pushed_at DESC`
- `ix_repo_language` on `language`

**Relationships:**
- `tags` -- many-to-many via RepoTag

#### UserTag

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | UUID | PK, default=uuid4 | |
| `name` | String(64) | NOT NULL, UNIQUE | |
| `color` | String(7) | NOT NULL | Hex color from fixed 16-color palette, e.g. `#3B82F6` |

**Indexes:**
- `uq_tag_name` UNIQUE on `name`

**Fixed color palette (16 colors):**
`#EF4444` (red), `#F97316` (orange), `#F59E0B` (amber), `#EAB308` (yellow), `#84CC16` (lime), `#22C55E` (green), `#10B981` (emerald), `#14B8A6` (teal), `#06B6D4` (cyan), `#3B82F6` (blue), `#6366F1` (indigo), `#8B5CF6` (violet), `#A855F7` (purple), `#D946EF` (fuchsia), `#EC4899` (pink), `#6B7280` (gray)

#### PaperTag (join)

| Column | Type | Constraints |
|--------|------|-------------|
| `paper_id` | UUID | FK → Paper.id ON DELETE CASCADE |
| `tag_id` | UUID | FK → UserTag.id ON DELETE CASCADE |

**Indexes:**
- `uq_paper_tag` UNIQUE on `(paper_id, tag_id)`

#### RepoTag (join)

| Column | Type | Constraints |
|--------|------|-------------|
| `repo_id` | UUID | FK → GitHubRepo.id ON DELETE CASCADE |
| `tag_id` | UUID | FK → UserTag.id ON DELETE CASCADE |

**Indexes:**
- `uq_repo_tag` UNIQUE on `(repo_id, tag_id)`

#### CrawlLog

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | UUID | PK, default=uuid4 | |
| `source` | String(32) | NOT NULL | Crawler name: `arxiv`, `github` |
| `started_at` | DateTime(UTC) | NOT NULL | |
| `finished_at` | DateTime(UTC) | nullable | NULL while running |
| `items_found` | Integer | default=0 | Total items fetched from source |
| `items_new` | Integer | default=0 | New items created (not previously seen) |
| `items_updated` | Integer | default=0 | Existing items updated |
| `status` | String(16) | NOT NULL, default=`running` | `running`, `success`, `partial`, `failed` |
| `error_message` | Text | nullable | Stack trace or error summary |

**Indexes:**
- `ix_crawl_log_source_started` on `(source, started_at DESC)`

#### Report

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | UUID | PK, default=uuid4 | |
| `type` | String(16) | NOT NULL | `daily`, `weekly` |
| `date_range_start` | Date | NOT NULL | |
| `date_range_end` | Date | NOT NULL | |
| `file_path` | String(2048) | NOT NULL | Relative path from project root, e.g. `reports/daily-2026-06-29.md` |
| `paper_count` | Integer | default=0 | Papers included |
| `repo_count` | Integer | default=0 | Repos included |
| `delivery_status` | String(16) | default=`pending` | `pending`, `delivered`, `failed` -- accommodates future delivery channels |
| `generated_at` | DateTime(UTC) | NOT NULL, default=utcnow | |

**Indexes:**
- `ix_report_type_generated` on `(type, generated_at DESC)`

### 3.3 SQLite FTS5 Setup

When the database URL is SQLite, the application startup creates the FTS5 virtual table and triggers:

```sql
CREATE VIRTUAL TABLE IF NOT EXISTS paper_fts USING fts5(
    title,
    abstract,
    content='paper',
    content_rowid='id'
);

-- Triggers to keep FTS in sync
CREATE TRIGGER IF NOT EXISTS paper_ai AFTER INSERT ON paper BEGIN
    INSERT INTO paper_fts(rowid, title, abstract) VALUES (new.id, new.title, new.abstract);
END;

CREATE TRIGGER IF NOT EXISTS paper_ad AFTER DELETE ON paper BEGIN
    INSERT INTO paper_fts(paper_fts, rowid, title, abstract) VALUES ('delete', old.id, old.title, old.abstract);
END;

CREATE TRIGGER IF NOT EXISTS paper_au AFTER UPDATE ON paper BEGIN
    INSERT INTO paper_fts(paper_fts, rowid, title, abstract) VALUES ('delete', old.id, old.title, old.abstract);
    INSERT INTO paper_fts(rowid, title, abstract) VALUES (new.id, new.title, new.abstract);
END;
```

For PostgreSQL, replace with a `search_vector` tsvector column and a GIN index. The service layer abstracts which search backend is used.

### 3.4 Dedup Merge Strategy

When a new paper is ingested, the system:

1. Checks `(source, source_id)` uniqueness -- if exists, update (upsert).
2. After upsert, checks `title_normalized` similarity against papers from OTHER sources:
   - Compute normalized Levenshtein ratio (Python `difflib.SequenceMatcher`).
   - If ratio >= 0.85, link the two papers as "versions" via a `paper_merge_id` foreign key (self-referential on Paper).
   - The merge relationship is stored as: `paper.merged_into_id` FK → Paper.id (nullable). The canonical record is the one with `merged_into_id IS NULL`.
3. This allows arxiv preprints and their conference versions (dblp/OpenReview) to be recognized as the same paper.

Add to Paper model:
- `merged_into_id` UUID nullable, FK → Paper.id, SET NULL on delete. Index on `merged_into_id`.

---

## 4. Route Design

All routes are prefixed with `/api/v1/`.

### 4.1 Papers

| Method | Path | Summary |
|--------|------|---------|
| `GET` | `/papers` | List papers with filters, search, pagination |
| `GET` | `/papers/{id}` | Get paper detail (includes authors, categories, tags) |
| `PUT` | `/papers/{id}/tags` | Set tags on a paper (replaces current tags) |

### 4.2 Repositories

| Method | Path | Summary |
|--------|------|---------|
| `GET` | `/repos` | List repos with filters, pagination |
| `GET` | `/repos/{id}` | Get repo detail (includes tags) |
| `PUT` | `/repos/{id}/tags` | Set tags on a repo |

### 4.3 Tags

| Method | Path | Summary |
|--------|------|---------|
| `GET` | `/tags` | List all tags |
| `POST` | `/tags` | Create a new tag |
| `PUT` | `/tags/{id}` | Update tag name/color |
| `DELETE` | `/tags/{id}` | Delete a tag (removes from all papers/repos) |

### 4.4 Reports

| Method | Path | Summary |
|--------|------|---------|
| `GET` | `/reports` | List reports, filterable by type |
| `GET` | `/reports/{id}` | Get report metadata + rendered Markdown content |
| `POST` | `/reports/{id}/retry` | Regenerate a specific report (re-runs template with same date range) |

### 4.5 Crawl Management

| Method | Path | Summary |
|--------|------|---------|
| `GET` | `/crawls/logs` | Paginated crawl log history |
| `GET` | `/crawls/status` | Current scheduler status (which jobs are registered, next run times) |
| `POST` | `/crawls/trigger/{source}` | Manually trigger a crawl for a specific source |

### 4.6 Categories

| Method | Path | Summary |
|--------|------|---------|
| `GET` | `/categories` | List all distinct categories (used to populate filter dropdowns) |

### 4.7 Authors

| Method | Path | Summary |
|--------|------|---------|
| `GET` | `/authors` | List authors (paginated, searchable by name) |
| `GET` | `/authors/{id}` | Author detail with their papers |

### 4.8 System

| Method | Path | Summary |
|--------|------|---------|
| `GET` | `/health` | Health check (DB connectivity, scheduler status) |
| `GET` | `/stats` | Dashboard stats: total papers, repos, tags, last crawl times, category distribution |

---

## 5. Crawler Plugin Architecture

### 5.1 Base Interface

Each crawler implements the `BaseCrawler` abstract base class:

```python
class BaseCrawler(ABC):
    """All crawlers implement this interface. Adding a new source requires
    only a subclass + registry registration -- no core code changes."""

    source: str                          # e.g. "arxiv", "github"
    delay_seconds: float = 1.0           # Polite delay between requests

    @abstractmethod
    async def fetch(self, params: dict) -> list[dict]:
        """Fetch raw data from the source API. Returns a list of raw item dicts."""
        ...

    @abstractmethod
    def normalize(self, raw: dict) -> dict:
        """Convert one raw item into the unified model dict. Returns a dict
        suitable for SQLAlchemy model construction or upsert."""
        ...

    @abstractmethod
    async def run(self, db: AsyncSession) -> CrawlLog:
        """Template method: fetch -> normalize -> upsert -> log.
        Returns a populated CrawlLog record."""
        ...
```

### 5.2 Registry

```python
class CrawlerRegistry:
    """Singleton registry mapping source names to crawler classes."""
    _crawlers: dict[str, type[BaseCrawler]] = {}

    @classmethod
    def register(cls, crawler_class: type[BaseCrawler]):
        cls._crawlers[crawler_class.source] = crawler_class

    @classmethod
    def get(cls, source: str) -> type[BaseCrawler]:
        return cls._crawlers[source]

    @classmethod
    def list_all(cls) -> list[str]:
        return list(cls._crawlers.keys())
```

### 5.3 ArxivCrawler

- **API:** `http://export.arxiv.org/api/query`
- **Categories queried:** `cs.CV`, `cs.AI`, `cs.LG`, `cs.MM`, `cs.CL`
- **Query strategy:** Query each category for papers added in the last 6 hours (or since last crawl), sorted by `submittedDate`.
- **Delay:** 3 seconds between requests (polite-use policy).
- **Normalization:** Parses ATOM XML response. Maps `arxiv:primary_category` to Category. Extracts author list from `<author>` elements.
- **Dedup:** `source="arxiv"`, `source_id` = arxiv ID (e.g. `2301.12345v2`).

### 5.4 GitHubCrawler

- **API:** `https://api.github.com/search/repositories` + `https://api.github.com/trending`
- **Topics queried:** `computer-vision`, `deep-learning`, `object-detection`, `image-segmentation`, `generative-models`, `nerf`, `3d-vision`, `multimodal`, `video-understanding`
- **Auth:** Bearer token via `GITHUB_TOKEN` environment variable.
- **Rate limiting:** 429 response triggers exponential backoff with jitter (1s, 2s, 4s, 8s, max 60s). Secondary rate limit respected via `Retry-After` header.
- **Normalization:** Maps `full_name`, `description`, `html_url` → `url`, `stargazers_count` → `stars`, `topics` (list), `pushed_at`.
- **Dedup:** `full_name` UNIQUE. On existing record, update `stars`, `forks`, `pushed_at`, `last_crawled_at`.
- **Frequency:** Configurable via `CRAWLER_GITHUB_INTERVAL_MINUTES`, default 120 (2 hours).

### 5.5 Adding a New Crawler (Future)

1. Create `backend/app/crawlers/new_source.py` with a class extending `BaseCrawler`.
2. Register it in `backend/app/crawlers/__init__.py`: `CrawlerRegistry.register(NewSourceCrawler)`.
3. Add a scheduler job in `engine/scheduler.py` for the new source.
4. Optionally add a new `source` value enum entry -- no model changes needed (source is a freeform string).
5. Run Alembic migration only if the new source requires additional model fields.

---

## 6. Report Engine Design

### 6.1 Generation Pipeline

```
Scheduler triggers (cron)
    │
    ▼
report_generator.generate(type: "daily" | "weekly")
    │
    ├── 1. Query DB for the report's date range
    │      - daily: [today 00:00, today 23:59]
    │      - weekly: [last Monday 00:00, this Sunday 23:59]
    │
    ├── 2. Collect data
    │      - New papers in range, grouped by category, sorted by a simple
    │        relevance heuristic (title keyword match against CV topics)
    │      - Trending repos (highest star gain since last report)
    │      - Category distribution counts
    │
    ├── 3. Render Markdown via Jinja2
    │      - Template: engine/templates/{type}.md.j2
    │      - Variables passed: papers, repos, stats, date_range, generated_at
    │
    ├── 4. Write to file
    │      - Path: reports/{type}-{date_range_end}.md
    │      - Reports are appended, never overwritten
    │
    └── 5. Persist Report record
           - delivery_status = "delivered" (filesystem delivery succeeded)
           - On failure: delivery_status = "failed", error logged
```

### 6.2 Report Content

**Daily Report** (`templates/daily.md.j2`):
- Header with date
- Section: New Papers Today (top 20, grouped by category)
- Section: Trending GitHub Repos (new today, sorted by stars)
- Section: Category Breakdown (count per category)
- Footer: generation timestamp

**Weekly Report** (`templates/weekly.md.j2`):
- Header with week range
- Section: Weekly Top Papers (top 30 across all categories)
- Section: Rising Repos (highest star gain this week)
- Section: Category Statistics (papers per category, week-over-week delta)
- Section: New Repos This Week
- Footer: generation timestamp

### 6.3 Scheduling

Job registration in `engine/scheduler.py`:

| Job Name | Trigger | Cron | Function |
|----------|---------|------|----------|
| `crawl_arxiv` | cron | `0 */6 * * *` (every 6h) | Run ArxivCrawler |
| `crawl_github` | cron | from `CRAWLER_GITHUB_INTERVAL_MINUTES` | Run GitHubCrawler |
| `report_daily` | cron | `0 22 * * *` (10 PM daily) | Generate daily report |
| `report_weekly` | cron | `0 10 * * 1` (Mon 10 AM) | Generate weekly report |

Each crawl job wraps the crawler's `run()` in try/except -- a single crawler failure logs to CrawlLog and does not disrupt the scheduler or other crawlers.

---

## 7. Config Management

### 7.1 Configuration Sources (priority order)

1. Environment variables (highest priority)
2. `.env` file in project root
3. Default values in `config.py`

### 7.2 Settings Schema (Pydantic `BaseSettings`)

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `DATABASE_URL` | str | `sqlite+aiosqlite:///./data/app.db` | SQLAlchemy connection string |
| `GITHUB_TOKEN` | str | `""` | GitHub personal access token for API auth |
| `CRAWLER_ARXIV_ENABLED` | bool | `true` | Enable/disable arxiv crawler |
| `CRAWLER_ARXIV_INTERVAL_MINUTES` | int | `360` | Arxiv crawl interval (6 hours) |
| `CRAWLER_ARXIV_DELAY_SECONDS` | float | `3.0` | Delay between arxiv API requests |
| `CRAWLER_GITHUB_ENABLED` | bool | `true` | Enable/disable GitHub crawler |
| `CRAWLER_GITHUB_INTERVAL_MINUTES` | int | `120` | GitHub crawl interval (2 hours) |
| `CRAWLER_GITHUB_DELAY_SECONDS` | float | `2.0` | Delay between GitHub API requests |
| `REPORT_OUTPUT_DIR` | str | `./reports` | Directory for generated Markdown reports |
| `REPORT_DAILY_CRON` | str | `0 22 * * *` | Cron expression for daily report |
| `REPORT_WEEKLY_CRON` | str | `0 10 * * 1` | Cron expression for weekly report |
| `LOG_LEVEL` | str | `INFO` | Python logging level |
| `API_CORS_ORIGINS` | str | `http://localhost:5173` | Comma-separated CORS allowed origins |

### 7.3 Config Class

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "sqlite+aiosqlite:///./data/app.db"
    github_token: str = ""
    crawler_arxiv_enabled: bool = True
    crawler_arxiv_interval_minutes: int = 360
    crawler_arxiv_delay_seconds: float = 3.0
    crawler_github_enabled: bool = True
    crawler_github_interval_minutes: int = 120
    crawler_github_delay_seconds: float = 2.0
    report_output_dir: str = "./reports"
    report_daily_cron: str = "0 22 * * *"
    report_weekly_cron: str = "0 10 * * 1"
    log_level: str = "INFO"
    api_cors_origins: str = "http://localhost:5173"
```

---

## 8. Frontend Architecture

### 8.1 Component Tree

```
<App>
  <BrowserRouter>
    <AppShell>                       # Sidebar + content layout
      <Sidebar>                      # Navigation links: Papers, Repos, Tags, Reports, Crawls
      <main>
        <Routes>
          <Route path="/" element={<PaperListPage />} />
          <Route path="/papers" element={<PaperListPage />} />
          <Route path="/papers/:id" element={<PaperDetailPage />} />
          <Route path="/repos" element={<RepoListPage />} />
          <Route path="/repos/:id" element={<RepoDetailPage />} />
          <Route path="/tags" element={<TagManagePage />} />
          <Route path="/reports" element={<ReportListPage />} />
          <Route path="/reports/:id" element={<ReportViewPage />} />
          <Route path="/crawls" element={<CrawlStatusPage />} />
        </Routes>
      </main>
    </AppShell>
  </BrowserRouter>
```

### 8.2 State Management

No global state library (Redux, Zustand) needed for V1. Each page fetches its own data via custom hooks (`usePapers`, `useRepos`, etc.) which call the API client layer and manage loading/error/data state locally with `useState` + `useEffect`.

### 8.3 Routing

React Router v6 with the following routes:

| Path | Page | Description |
|------|------|-------------|
| `/` | PaperListPage | Redirect or default to papers |
| `/papers` | PaperListPage | Paper browsing with filters |
| `/papers/:id` | PaperDetailPage | Single paper detail |
| `/repos` | RepoListPage | Repo browsing with filters |
| `/repos/:id` | RepoDetailPage | Single repo detail |
| `/tags` | TagManagePage | CRUD tag management |
| `/reports` | ReportListPage | Report history list |
| `/reports/:id` | ReportViewPage | Inline Markdown report view |
| `/crawls` | CrawlStatusPage | Crawl log history + scheduler status + manual trigger |

### 8.4 API Client Layer

All API calls go through `api/client.ts` -- a configured axios instance:

```typescript
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1",
  timeout: 15000,
  headers: { "Content-Type": "application/json" },
});

// Response interceptor: unwrap data, normalize errors
// Error format: { error: { code: string, message: string, details?: object } }
```

Each resource has its own API module (e.g. `api/papers.ts`) exporting typed functions:

```typescript
export async function listPapers(params: PaperQueryParams): Promise<PaginatedResponse<PaperSummary>>
export async function getPaper(id: string): Promise<PaperDetail>
export async function setPaperTags(id: string, tagIds: string[]): Promise<void>
```

---

## 9. Deployment

### 9.1 Development Mode

- **Backend:** `uvicorn app.main:app --reload` on port 8000
- **Frontend:** `vite dev` on port 5173 with proxy to `localhost:8000`
- **Database:** SQLite file at `data/app.db`

### 9.2 Production Mode (Docker Compose)

```yaml
services:
  api:
    build: ./backend
    ports: ["8000:8000"]
    environment: *env
    volumes: ["./data:/app/data", "./reports:/app/reports"]

  frontend:
    build: ./frontend
    ports: ["80:80"]
    depends_on: [api]

  # Optional: replace SQLite with PostgreSQL
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: paper_crawler
      POSTGRES_USER: crawler
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes: ["pgdata:/var/lib/postgresql/data"]
    profiles: ["postgres"]
```

### 9.3 Data Persistence

- SQLite: `data/` directory mounted as volume
- PostgreSQL: named volume `pgdata`
- Reports: `reports/` directory mounted as volume
- No cloud dependencies; fully offline capable after `docker compose pull`
