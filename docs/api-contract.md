# API Contract — Paper + GitHub Knowledge Crawler

**Version:** 1.0.0  
**Base URL:** `/api/v1`  
**Content-Type:** `application/json`

---

## 1. Conventions

### 1.1 Pagination

All list endpoints accept the following query parameters:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | integer | `1` | Page number (1-indexed) |
| `page_size` | integer | `20` | Items per page (max 100) |

Paginated response shape:

```json
{
  "items": [],
  "total": 150,
  "page": 1,
  "page_size": 20,
  "pages": 8
}
```

### 1.2 Error Responses

All errors follow this shape:

```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Paper with id 550e8400-e29b-41d4-a716-446655440000 not found",
    "details": {}
  }
}
```

**Error codes:**

| Code | HTTP Status | Meaning |
|------|-------------|---------|
| `VALIDATION_ERROR` | 422 | Request body or query params failed Pydantic validation |
| `RESOURCE_NOT_FOUND` | 404 | Requested resource does not exist |
| `RESOURCE_CONFLICT` | 409 | Duplicate tag name, duplicate source_id, etc. |
| `CRAWLER_BUSY` | 409 | A crawl for this source is already running |
| `CRAWLER_NOT_FOUND` | 404 | Unknown crawler source name |
| `INTERNAL_ERROR` | 500 | Unhandled server error |

### 1.3 Date/Time Formats

- Dates: `YYYY-MM-DD` (ISO 8601 date)
- Timestamps: `YYYY-MM-DDTHH:MM:SSZ` (ISO 8601 UTC)

### 1.4 Null Handling

Fields that may not have data are `null` in JSON responses, never absent.

---

## 2. Papers

### GET /papers

List papers with filters, full-text search, and pagination.

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page` | integer | no | Default 1 |
| `page_size` | integer | no | Default 20, max 100 |
| `source` | string | no | Filter by source. Repeatable: `?source=arxiv&source=dblp` |
| `category` | string | no | Filter by category name. Repeatable. |
| `date_from` | date | no | Inclusive start date for `published_date` |
| `date_to` | date | no | Inclusive end date for `published_date` |
| `q` | string | no | Full-text search on title and abstract (SQLite FTS5) |
| `tag_id` | UUID | no | Filter papers having this tag. Repeatable. |
| `sort` | string | no | Sort field: `published_date` (default), `crawled_at`, `title`. Prefix `-` for descending. |
| `venue` | string | no | Filter by venue name (partial match) |

**Response:** `200 OK`

```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Denoising Diffusion Probabilistic Models",
      "source": "arxiv",
      "source_id": "2006.11239",
      "venue": "NeurIPS 2020",
      "published_date": "2020-06-19",
      "url": "https://arxiv.org/abs/2006.11239",
      "pdf_url": "https://arxiv.org/pdf/2006.11239.pdf",
      "code_url": "https://github.com/hojonathanho/diffusion",
      "crawled_at": "2026-06-29T14:30:00Z",
      "updated_at": "2026-06-29T14:30:00Z",
      "categories": [
        { "id": "uuid", "name": "cs.CV", "source": "arxiv" }
      ],
      "tags": [
        { "id": "uuid", "name": "diffusion", "color": "#3B82F6" }
      ],
      "author_names": ["Jonathan Ho", "Ajay Jain", "Pieter Abbeel"]
    }
  ],
  "total": 150,
  "page": 1,
  "page_size": 20,
  "pages": 8
}
```

---

### GET /papers/{id}

Get a single paper with full detail.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | UUID | Paper ID |

**Response:** `200 OK`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Denoising Diffusion Probabilistic Models",
  "abstract": "We present high quality image synthesis results using diffusion models...",
  "source": "arxiv",
  "source_id": "2006.11239",
  "venue": "NeurIPS 2020",
  "published_date": "2020-06-19",
  "url": "https://arxiv.org/abs/2006.11239",
  "pdf_url": "https://arxiv.org/pdf/2006.11239.pdf",
  "code_url": "https://github.com/hojonathanho/diffusion",
  "crawled_at": "2026-06-29T14:30:00Z",
  "updated_at": "2026-06-29T14:30:00Z",
  "authors": [
    { "id": "uuid", "name": "Jonathan Ho", "affiliation": "UC Berkeley", "author_order": 0 },
    { "id": "uuid", "name": "Ajay Jain", "affiliation": "UC Berkeley", "author_order": 1 }
  ],
  "categories": [
    { "id": "uuid", "name": "cs.CV", "source": "arxiv" },
    { "id": "uuid", "name": "cs.LG", "source": "arxiv" }
  ],
  "tags": [
    { "id": "uuid", "name": "diffusion", "color": "#3B82F6" },
    { "id": "uuid", "name": "generative", "color": "#22C55E" }
  ],
  "merged_into_id": null,
  "versions": []
}
```

`versions` lists other paper records whose `merged_into_id` points to this paper (e.g., the arxiv preprint version of a conference paper). Empty if none.

**Errors:**
- `404` -- Paper not found

---

### PUT /papers/{id}/tags

Replace the set of tags assigned to this paper.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | UUID | Paper ID |

**Request Body:**

```json
{
  "tag_ids": [
    "550e8400-e29b-41d4-a716-446655440001",
    "550e8400-e29b-41d4-a716-446655440002"
  ]
}
```

**Response:** `200 OK`

```json
{
  "paper_id": "550e8400-e29b-41d4-a716-446655440000",
  "tags": [
    { "id": "uuid", "name": "diffusion", "color": "#3B82F6" },
    { "id": "uuid", "name": "generative", "color": "#22C55E" }
  ]
}
```

**Errors:**
- `404` -- Paper not found or tag_id not found

---

## 3. Repositories

### GET /repos

List GitHub repos with filters and pagination.

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page` | integer | no | Default 1 |
| `page_size` | integer | no | Default 20, max 100 |
| `language` | string | no | Filter by language. Repeatable: `?language=Python&language=Rust` |
| `topic` | string | no | Filter by topic tag. Repeatable. |
| `stars_min` | integer | no | Minimum stars |
| `stars_max` | integer | no | Maximum stars |
| `pushed_after` | timestamp | no | Only repos pushed after this time |
| `pushed_before` | timestamp | no | Only repos pushed before this time |
| `tag_id` | UUID | no | Filter repos having this tag. Repeatable. |
| `q` | string | no | Search in `full_name` and `description` (SQL LIKE) |
| `sort` | string | no | Sort field: `stars` (default desc), `forks`, `pushed_at`, `crawled_at`. Prefix `-` for descending. |

**Response:** `200 OK`

```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "full_name": "hojonathanho/diffusion",
      "description": "Denoising Diffusion Probabilistic Models",
      "url": "https://github.com/hojonathanho/diffusion",
      "stars": 4500,
      "forks": 520,
      "language": "Python",
      "topics": ["deep-learning", "generative-models", "image-generation"],
      "pushed_at": "2026-06-28T10:00:00Z",
      "crawled_at": "2026-06-29T14:00:00Z",
      "last_crawled_at": "2026-06-29T14:00:00Z",
      "tags": [
        { "id": "uuid", "name": "diffusion", "color": "#3B82F6" }
      ]
    }
  ],
  "total": 85,
  "page": 1,
  "page_size": 20,
  "pages": 5
}
```

---

### GET /repos/{id}

Get a single repo with full detail.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | UUID | Repo ID |

**Response:** `200 OK`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "full_name": "hojonathanho/diffusion",
  "description": "Denoising Diffusion Probabilistic Models",
  "url": "https://github.com/hojonathanho/diffusion",
  "stars": 4500,
  "forks": 520,
  "language": "Python",
  "topics": ["deep-learning", "generative-models", "image-generation"],
  "pushed_at": "2026-06-28T10:00:00Z",
  "crawled_at": "2026-06-29T14:00:00Z",
  "last_crawled_at": "2026-06-29T14:00:00Z",
  "tags": [
    { "id": "uuid", "name": "diffusion", "color": "#3B82F6" },
    { "id": "uuid", "name": "to-read", "color": "#F59E0B" }
  ]
}
```

**Errors:**
- `404` -- Repo not found

---

### PUT /repos/{id}/tags

Replace the set of tags assigned to this repo.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | UUID | Repo ID |

**Request Body:**

```json
{
  "tag_ids": [
    "550e8400-e29b-41d4-a716-446655440001"
  ]
}
```

**Response:** `200 OK`

```json
{
  "repo_id": "550e8400-e29b-41d4-a716-446655440000",
  "tags": [
    { "id": "uuid", "name": "diffusion", "color": "#3B82F6" }
  ]
}
```

**Errors:**
- `404` -- Repo not found or tag_id not found

---

## 4. Tags

### GET /tags

List all user-defined tags. Not paginated (small dataset).

**Response:** `200 OK`

```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "name": "diffusion",
      "color": "#3B82F6",
      "paper_count": 42,
      "repo_count": 15,
      "created_at": "2026-06-20T08:00:00Z"
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440002",
      "name": "to-read",
      "color": "#F59E0B",
      "paper_count": 7,
      "repo_count": 3,
      "created_at": "2026-06-20T08:05:00Z"
    }
  ]
}
```

---

### POST /tags

Create a new tag.

**Request Body:**

```json
{
  "name": "nerf-papers",
  "color": "#8B5CF6"
}
```

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `name` | string | yes | 1-64 characters, unique across all tags |
| `color` | string | yes | Must be one of the 16 palette colors |

**Response:** `201 Created`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440003",
  "name": "nerf-papers",
  "color": "#8B5CF6",
  "paper_count": 0,
  "repo_count": 0,
  "created_at": "2026-06-29T15:00:00Z"
}
```

**Errors:**
- `409` -- Tag name already exists
- `422` -- Color not in allowed palette

Valid palette: `#EF4444`, `#F97316`, `#F59E0B`, `#EAB308`, `#84CC16`, `#22C55E`, `#10B981`, `#14B8A6`, `#06B6D4`, `#3B82F6`, `#6366F1`, `#8B5CF6`, `#A855F7`, `#D946EF`, `#EC4899`, `#6B7280`

---

### PUT /tags/{id}

Update a tag's name and/or color.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | UUID | Tag ID |

**Request Body:** (all fields optional, only provided fields are updated)

```json
{
  "name": "nerf-research",
  "color": "#A855F7"
}
```

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `name` | string | no | 1-64 characters, unique |
| `color` | string | no | Must be one of the 16 palette colors |

**Response:** `200 OK`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440003",
  "name": "nerf-research",
  "color": "#A855F7",
  "paper_count": 0,
  "repo_count": 0,
  "created_at": "2026-06-29T15:00:00Z"
}
```

**Errors:**
- `404` -- Tag not found
- `409` -- Updated name conflicts with another tag

---

### DELETE /tags/{id}

Delete a tag. This removes the tag from all papers and repos that had it assigned.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | UUID | Tag ID |

**Response:** `204 No Content`

**Errors:**
- `404` -- Tag not found

---

## 5. Reports

### GET /reports

List generated reports.

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page` | integer | no | Default 1 |
| `page_size` | integer | no | Default 20, max 100 |
| `type` | string | no | Filter by type: `daily` or `weekly` |
| `sort` | string | no | Default `-generated_at` (newest first) |

**Response:** `200 OK`

```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440010",
      "type": "daily",
      "date_range_start": "2026-06-29",
      "date_range_end": "2026-06-29",
      "file_path": "reports/daily-2026-06-29.md",
      "paper_count": 23,
      "repo_count": 7,
      "delivery_status": "delivered",
      "generated_at": "2026-06-29T22:00:05Z"
    }
  ],
  "total": 14,
  "page": 1,
  "page_size": 20,
  "pages": 1
}
```

---

### GET /reports/{id}

Get report metadata plus rendered Markdown content.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | UUID | Report ID |

**Response:** `200 OK`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440010",
  "type": "daily",
  "date_range_start": "2026-06-29",
  "date_range_end": "2026-06-29",
  "file_path": "reports/daily-2026-06-29.md",
  "paper_count": 23,
  "repo_count": 7,
  "delivery_status": "delivered",
  "generated_at": "2026-06-29T22:00:05Z",
  "content": "# Daily Report — 2026-06-29\n\n## New Papers Today\n\n..."
}
```

The `content` field contains the raw Markdown string read from disk.

**Errors:**
- `404` -- Report not found
- `500` -- Report file missing from disk (metadata exists but file was deleted)

---

### POST /reports/{id}/retry

Regenerate a specific report using the same date range and type. This re-runs the report engine for the report's original date range and overwrites the file.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | UUID | Report ID |

**Response:** `200 OK` -- returns the full report object (same shape as GET /reports/{id}) with updated `generated_at` and counts.

**Errors:**
- `404` -- Report not found

---

## 6. Crawl Management

### GET /crawls/logs

Paginated crawl log history.

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page` | integer | no | Default 1 |
| `page_size` | integer | no | Default 20, max 100 |
| `source` | string | no | Filter by source: `arxiv`, `github` |
| `status` | string | no | Filter by status: `success`, `partial`, `failed` |
| `sort` | string | no | Default `-started_at` (newest first) |

**Response:** `200 OK`

```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440100",
      "source": "arxiv",
      "started_at": "2026-06-29T14:00:00Z",
      "finished_at": "2026-06-29T14:02:15Z",
      "items_found": 45,
      "items_new": 12,
      "items_updated": 33,
      "status": "success",
      "error_message": null
    }
  ],
  "total": 120,
  "page": 1,
  "page_size": 20,
  "pages": 6
}
```

---

### GET /crawls/status

Current scheduler status -- which crawlers are registered, enabled, next run times.

**Response:** `200 OK`

```json
{
  "jobs": [
    {
      "source": "arxiv",
      "enabled": true,
      "interval_minutes": 360,
      "last_run": "2026-06-29T14:00:00Z",
      "next_run": "2026-06-29T20:00:00Z",
      "last_status": "success"
    },
    {
      "source": "github",
      "enabled": true,
      "interval_minutes": 120,
      "last_run": "2026-06-29T15:00:00Z",
      "next_run": "2026-06-29T17:00:00Z",
      "last_status": "success"
    },
    {
      "source": "report_daily",
      "enabled": true,
      "cron": "0 22 * * *",
      "last_run": null,
      "next_run": "2026-06-29T22:00:00Z",
      "last_status": null
    },
    {
      "source": "report_weekly",
      "enabled": true,
      "cron": "0 10 * * 1",
      "last_run": null,
      "next_run": "2026-06-30T10:00:00Z",
      "last_status": null
    }
  ]
}
```

---

### POST /crawls/trigger/{source}

Manually trigger a crawl for a given source. Runs asynchronously; the endpoint returns immediately.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `source` | string | Crawler source name: `arxiv`, `github` |

**Response:** `202 Accepted`

```json
{
  "source": "arxiv",
  "message": "Crawl triggered. Check /crawls/logs for results.",
  "triggered_at": "2026-06-29T15:30:00Z"
}
```

**Errors:**
- `404` -- Unknown source (not registered)
- `409` -- Crawl already running for this source

---

## 7. Categories

### GET /categories

List all distinct categories. Not paginated.

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `source` | string | no | Filter by source: `arxiv`, `dblp`, `openreview` |

**Response:** `200 OK`

```json
{
  "items": [
    { "id": "uuid", "name": "cs.CV", "source": "arxiv", "paper_count": 1230 },
    { "id": "uuid", "name": "cs.AI", "source": "arxiv", "paper_count": 980 },
    { "id": "uuid", "name": "cs.LG", "source": "arxiv", "paper_count": 2100 }
  ]
}
```

---

## 8. Authors

### GET /authors

List authors with pagination.

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page` | integer | no | Default 1 |
| `page_size` | integer | no | Default 20, max 100 |
| `q` | string | no | Search by name (LIKE match) |

**Response:** `200 OK`

```json
{
  "items": [
    {
      "id": "uuid",
      "name": "Jonathan Ho",
      "affiliation": "UC Berkeley",
      "paper_count": 15
    }
  ],
  "total": 5000,
  "page": 1,
  "page_size": 20,
  "pages": 250
}
```

---

### GET /authors/{id}

Get a single author with their papers.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | UUID | Author ID |

**Response:** `200 OK`

```json
{
  "id": "uuid",
  "name": "Jonathan Ho",
  "affiliation": "UC Berkeley",
  "papers": [
    {
      "id": "uuid",
      "title": "Denoising Diffusion Probabilistic Models",
      "published_date": "2020-06-19",
      "source": "arxiv",
      "author_order": 0
    }
  ]
}
```

**Errors:**
- `404` -- Author not found

---

## 9. System

### GET /health

Health check. Returns 200 if the server and database are reachable.

**Response:** `200 OK`

```json
{
  "status": "ok",
  "timestamp": "2026-06-29T15:30:00Z",
  "database": "connected",
  "scheduler": "running",
  "version": "1.0.0"
}
```

---

### GET /stats

Dashboard statistics. Not paginated.

**Response:** `200 OK`

```json
{
  "papers": {
    "total": 12450,
    "by_source": { "arxiv": 10000, "dblp": 2000, "openreview": 450 },
    "new_today": 45,
    "new_this_week": 312
  },
  "repos": {
    "total": 890,
    "new_today": 12,
    "new_this_week": 85
  },
  "tags": {
    "total": 15
  },
  "crawls": {
    "last_arxiv": "2026-06-29T14:00:00Z",
    "last_github": "2026-06-29T15:00:00Z",
    "total_runs": 520,
    "success_rate": 0.97
  },
  "reports": {
    "daily_count": 30,
    "weekly_count": 4
  },
  "top_categories": [
    { "name": "cs.CV", "paper_count": 5200 },
    { "name": "cs.LG", "paper_count": 4800 }
  ],
  "top_languages": [
    { "language": "Python", "repo_count": 620 },
    { "language": "JavaScript", "repo_count": 45 }
  ]
}
```

---

## 10. Data Types Reference

### PaperSummary (list item)
| Field | Type | Nullable |
|-------|------|----------|
| `id` | UUID | no |
| `title` | string | no |
| `source` | string | no |
| `source_id` | string | no |
| `venue` | string | yes |
| `published_date` | date | yes |
| `url` | string | no |
| `pdf_url` | string | yes |
| `code_url` | string | yes |
| `crawled_at` | datetime | no |
| `updated_at` | datetime | no |
| `categories` | CategoryRef[] | no |
| `tags` | TagRef[] | no |
| `author_names` | string[] | no |

### PaperDetail (extends PaperSummary)
| Field | Type | Nullable |
|-------|------|----------|
| `abstract` | string | yes |
| `authors` | AuthorRef[] | no |
| `merged_into_id` | UUID | yes |
| `versions` | PaperVersionRef[] | no |

### PaperVersionRef
| Field | Type | Nullable |
|-------|------|----------|
| `id` | UUID | no |
| `title` | string | no |
| `source` | string | no |
| `url` | string | no |

### CategoryRef
| Field | Type | Nullable |
|-------|------|----------|
| `id` | UUID | no |
| `name` | string | no |
| `source` | string | no |

### AuthorRef
| Field | Type | Nullable |
|-------|------|----------|
| `id` | UUID | no |
| `name` | string | no |
| `affiliation` | string | yes |
| `author_order` | integer | no |

### AuthorWithPapers
| Field | Type | Nullable |
|-------|------|----------|
| `id` | UUID | no |
| `name` | string | no |
| `affiliation` | string | yes |
| `papers` | AuthorPaperRef[] | no |

### AuthorPaperRef
| Field | Type | Nullable |
|-------|------|----------|
| `id` | UUID | no |
| `title` | string | no |
| `published_date` | date | yes |
| `source` | string | no |
| `author_order` | integer | no |

### RepoSummary (list item)
| Field | Type | Nullable |
|-------|------|----------|
| `id` | UUID | no |
| `full_name` | string | no |
| `description` | string | yes |
| `url` | string | no |
| `stars` | integer | no |
| `forks` | integer | no |
| `language` | string | yes |
| `topics` | string[] | no |
| `pushed_at` | datetime | yes |
| `crawled_at` | datetime | no |
| `last_crawled_at` | datetime | no |
| `tags` | TagRef[] | no |

### RepoDetail (same as RepoSummary, no additional fields in V1)

### TagRef
| Field | Type | Nullable |
|-------|------|----------|
| `id` | UUID | no |
| `name` | string | no |
| `color` | string | no |

### TagDetail
| Field | Type | Nullable |
|-------|------|----------|
| `id` | UUID | no |
| `name` | string | no |
| `color` | string | no |
| `paper_count` | integer | no |
| `repo_count` | integer | no |
| `created_at` | datetime | no |

### ReportSummary (list item)
| Field | Type | Nullable |
|-------|------|----------|
| `id` | UUID | no |
| `type` | string | no |
| `date_range_start` | date | no |
| `date_range_end` | date | no |
| `file_path` | string | no |
| `paper_count` | integer | no |
| `repo_count` | integer | no |
| `delivery_status` | string | no |
| `generated_at` | datetime | no |

### ReportDetail (extends ReportSummary)
| Field | Type | Nullable |
|-------|------|----------|
| `content` | string | no |

### CrawlLogEntry
| Field | Type | Nullable |
|-------|------|----------|
| `id` | UUID | no |
| `source` | string | no |
| `started_at` | datetime | no |
| `finished_at` | datetime | yes |
| `items_found` | integer | no |
| `items_new` | integer | no |
| `items_updated` | integer | no |
| `status` | string | no |
| `error_message` | string | yes |

### CrawlStatus
| Field | Type | Nullable |
|-------|------|----------|
| `source` | string | no |
| `enabled` | boolean | no |
| `interval_minutes` | integer | yes |
| `cron` | string | yes |
| `last_run` | datetime | yes |
| `next_run` | datetime | yes |
| `last_status` | string | yes |

### PaginatedResponse<T>
| Field | Type | Nullable |
|-------|------|----------|
| `items` | T[] | no |
| `total` | integer | no |
| `page` | integer | no |
| `page_size` | integer | no |
| `pages` | integer | no |

### ApiError
| Field | Type | Nullable |
|-------|------|----------|
| `error.code` | string | no |
| `error.message` | string | no |
| `error.details` | object | no |

### StatsResponse
| Field | Type | Nullable |
|-------|------|----------|
| `papers` | PaperStats | no |
| `repos` | RepoStats | no |
| `tags` | TagStats | no |
| `crawls` | CrawlStats | no |
| `reports` | ReportStats | no |
| `top_categories` | CategoryCount[] | no |
| `top_languages` | LanguageCount[] | no |

---

## 11. Request/Response Headers

**All requests:**
```
Content-Type: application/json
Accept: application/json
```

**All responses:**
```
Content-Type: application/json
X-Request-Id: <uuid>
```
