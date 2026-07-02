# Requirements — Paper + GitHub 知识爬虫系统

**Author:** PM
**Date:** 2026-06-29
**Status:** Draft

---

## Overview

A local-first automated crawling system that monitors computer vision research across arxiv, GitHub, Papers With Code, and major conference proceedings (CVPR, ICCV, NeurIPS, etc.). The system ingests papers and repositories on a schedule, normalizes them into a unified database, exposes a React web panel for browsing, filtering, and tagging, and generates daily/weekly Markdown reports delivered to the local filesystem. Built as a modular monolith (Python FastAPI + React) with a plugin-based crawler registry so new sources can be added with minimal effort.

---

## User Stories

### P0 — Must ship in V1

**1. Automated arxiv Crawling**
As a CV researcher, I want the system to automatically fetch the latest papers from arxiv (cs.CV, cs.AI, cs.LG, cs.MM, cs.CL) every 6 hours so that I never miss new submissions in my field.
- Normalize raw arxiv API responses into the unified Paper model.
- De-duplicate via unique `(source, source_id)` index.
- Log every crawl run (items found, status, errors) to CrawlLog.

**2. Automated GitHub Repository Crawling**
As a researcher who follows open-source CV projects, I want the system to crawl GitHub Trending and specific topics (computer-vision, deep-learning, object-detection, etc.) every 2 hours so that promising repos surface quickly.
- Use GitHub API with token-based auth.
- Handle 429 rate limiting with automatic backoff-retry.
- De-duplicate by `full_name`; detect updates via `pushed_at`.

**3. Paper Browsing and Filtering**
As a researcher, I want to browse crawled papers in a web panel with filters by source, category, date range, and keyword so that I can efficiently find work relevant to my interests.
- Multi-select filters for source (arxiv, pwc, dblp) and CV subfield category.
- Date-range picker bound to `published_date`.
- Full-text keyword search across title and abstract.
- Results displayed as a paginated, sortable list with clickable external links.

**4. GitHub Repository Browsing and Filtering**
As a researcher, I want to browse crawled GitHub repos in the web panel with filters by language, topic, stars, and recency so that I can discover high-quality implementations.
- Sortable columns: stars, forks, pushed_at.
- Filter by programming language (multi-select).
- Filter by topic tags (multi-select).
- Clickable links to the repo on GitHub.

**5. Tag Management**
As a user, I want to create, edit, and assign custom tags (with colors) to papers and repositories so that I can build my own organizational taxonomy.
- CRUD for tags (name + color hex).
- Assign/unassign tags to papers (many-to-many via PaperTag).
- Assign/unassign tags to repos (many-to-many via RepoTag).
- Filter papers and repos by tag in the browse views.

**6. Scheduled Daily Report**
As a researcher, I want the system to generate a Markdown report every evening at 22:00 that summarizes the day's new papers and trending repos so that I can review the day's developments in one place.
- Report includes: top new papers (by relevance/novelty), new trending GitHub repos, category breakdown.
- Report saved to `reports/` directory with a predictable filename.
- Report metadata persisted to the Report table.
- Report viewable inline in the web panel (Markdown renderer).

**7. Scheduled Weekly Report**
As a researcher, I want the system to generate a comprehensive Markdown report every Monday at 10:00 summarizing the week's highlights, rising projects, and per-category statistics so that I can get a curated weekly digest.
- Report includes: weekly top papers, rising repos (biggest star gain), category distribution stats.
- Same delivery mechanism as daily report.

**8. Report History and Viewing**
As a user, I want to browse past generated reports in the web panel so that I can revisit previous summaries.
- List view of all reports with type, date range, paper/repo counts, generation timestamp.
- Click a report to render its Markdown inline.

### P1 — Should ship soon after V1

**9. Papers With Code Crawling**
As a researcher, I want the system to crawl Papers With Code daily for the latest papers and leaderboard changes so that I can track state-of-the-art results alongside publications.
- Crawl PWC "latest papers" listing and selected leaderboard pages.
- Link papers to their code_url when available in PWC metadata.

**10. Conference Proceedings Crawling**
As a researcher, I want the system to crawl conference proceedings from dblp and OpenReview every 3 days for CVPR, ICCV, ECCV, NeurIPS, ICML, ICLR, and AAAI so that I see top-venue papers as soon as proceedings are posted.
- Parse dblp venue pages for accepted paper lists.
- Optionally query OpenReview for peer-reviewed venues.
- Map conference papers to the unified Paper model with venue field populated.

**11. Author Information Tracking**
As a researcher, I want author names and affiliations extracted and linked to papers so that I can follow specific researchers across venues.
- Populate Author and PaperAuthor tables during normalization.
- Display author list on paper detail view.
- Future: filter papers by author.

**12. Advanced Search**
As a power user, I want to combine multiple filters (source + category + tag + date + keyword + author) in a single query so that I can narrow results precisely.
- API supports query parameters for all filter dimensions.
- Frontend search bar with filter chips that stack.

### P2 — Future iterations

**13. Custom Alert Rules**
As a user, I want to define keyword-based alert rules (e.g., "new paper with 'diffusion models' in title") that trigger notifications so that I catch high-signal work immediately.

**14. Export Functionality**
As a user, I want to export filtered paper/repo lists as BibTeX, CSV, or Markdown so that I can use them in my own reference manager or share with colleagues.

**15. Statistics Dashboard**
As a user, I want a dashboard showing crawl stats, category trends, and source activity over time so that I can understand the system's coverage and my field's publication patterns.

**16. Multi-user Support**
As a lab lead, I want multiple researchers to have their own tag sets and saved views so that the system can serve a small team without interference.

**17. Mobile-responsive Layout**
As a user who occasionally checks on my phone, I want the web panel to be usable on a mobile screen so that I can browse papers during commutes.

---

## Non-functional Requirements

### Performance
- Crawl jobs must not block the API: all crawls run as async background tasks (FastAPI BackgroundTasks or APScheduler jobs).
- Paper list queries must return in under 500ms for 10k+ records with filters applied (indexes on `published_date`, `source`, category join).
- Frontend bundle size under 500 KB gzipped (Vite tree-shaking + code splitting).
- Report generation for a day's worth of papers completes in under 5 seconds.

### Reliability
- A single crawler failure must not crash the scheduler or affect other crawlers (try/except per crawler, logged to CrawlLog with status=partial/failed).
- Database transactions use upsert semantics (ON CONFLICT DO UPDATE) so duplicate crawl runs are idempotent.
- GitHub API rate limiting is handled gracefully: exponential backoff with jitter, token rotation support.
- All crawl failures are logged with `error_message` in CrawlLog; the scheduler emits a summary log line after each run cycle.

### Extensibility
- Adding a new data source requires only: (a) a new class implementing `BaseCrawler`, (b) registration in the Crawler Registry. No core code changes.
- New model fields added via Alembic migrations; the ORM layer insulates application code.
- Frontend components use a shared filter-bar pattern so new filter dimensions are drop-in.
- Report templates are Jinja2 files in a `templates/` directory -- adding a new report type is a new template + a scheduler entry.

### Data Integrity
- `source + source_id` is the canonical identity for papers; `full_name` for repos. Unique indexes enforce this at the database level.
- All timestamps stored in UTC.
- Foreign key constraints enforce referential integrity between Paper/Author/Category/Repo and their join tables.
- CrawlLog provides an audit trail: every crawl run has a started_at, finished_at, items_found, and status.

### Local-first, Deployable
- Default configuration uses SQLite with WAL mode for zero-setup local use.
- One config flag switches to PostgreSQL for server deployment.
- All components (API, scheduler, frontend) run from a single `docker-compose up`.
- No cloud dependencies; works fully offline after initial dependency install.

---

## Out of Scope (V1)

- User authentication, login, or role-based access control.
- Full-text PDF parsing and content extraction.
- Social sharing features (share paper link, comment threads).
- Mobile-responsive design (desktop-first; P2).
- Citation graph construction or citation count tracking.
- Integration with reference managers (Zotero, Mendeley).
- Email or push notification delivery of reports (file-based only in V1).
- CI/CD pipeline for automated testing and deployment.
- Paper recommendation engine or ML-based relevance ranking.
- Multi-language support (UI is Chinese/English bilingual as needed, but no i18n framework).
