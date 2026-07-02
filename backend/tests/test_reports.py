"""Tests for Report API endpoints."""

import os
from datetime import date

import pytest

from app.models.report import Report


@pytest.mark.asyncio
async def test_get_reports_empty(client):
    """GET /reports returns empty list when no reports exist."""
    response = await client.get("/api/v1/reports")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []


@pytest.mark.asyncio
async def test_get_reports_with_data(client, db_session):
    """GET /reports returns seeded reports."""
    reports = [
        Report(
            id="report-1",
            type="daily",
            date_range_start=date(2024, 1, 15),
            date_range_end=date(2024, 1, 15),
            file_path="/tmp/report-1.md",
            paper_count=5,
            repo_count=2,
            delivery_status="delivered",
        ),
        Report(
            id="report-2",
            type="weekly",
            date_range_start=date(2024, 1, 8),
            date_range_end=date(2024, 1, 14),
            file_path="/tmp/report-2.md",
            paper_count=20,
            repo_count=8,
            delivery_status="delivered",
        ),
    ]
    for r in reports:
        db_session.add(r)
    await db_session.flush()

    response = await client.get("/api/v1/reports")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_get_report_by_id_found(client, db_session):
    """GET /reports/{id} returns report with content if file exists."""
    # Create a temp file for the report
    import tempfile
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    ) as f:
        f.write("# Test Report\nContent here.")
        file_path = f.name

    report = Report(
        id="report-3",
        type="daily",
        date_range_start=date(2024, 1, 15),
        date_range_end=date(2024, 1, 15),
        file_path=file_path,
        paper_count=3,
        repo_count=1,
        delivery_status="delivered",
    )
    db_session.add(report)
    await db_session.flush()

    try:
        response = await client.get("/api/v1/reports/report-3")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "report-3"
        assert data["type"] == "daily"
        assert "# Test Report" in data["content"]
    finally:
        os.unlink(file_path)


@pytest.mark.asyncio
async def test_get_report_by_id_not_found(client):
    """GET /reports/{id} returns 404 for unknown id."""
    response = await client.get("/api/v1/reports/nonexistent")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_retry_report_not_found(client):
    """POST /reports/{id}/retry returns 404 for unknown id."""
    response = await client.post("/api/v1/reports/nonexistent/retry")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_reports_filter_by_type(client, db_session):
    """GET /reports?type=daily filters correctly."""
    reports = [
        Report(
            id="report-4",
            type="daily",
            date_range_start=date(2024, 1, 15),
            date_range_end=date(2024, 1, 15),
            file_path="/tmp/r4.md",
        ),
        Report(
            id="report-5",
            type="weekly",
            date_range_start=date(2024, 1, 8),
            date_range_end=date(2024, 1, 14),
            file_path="/tmp/r5.md",
        ),
    ]
    for r in reports:
        db_session.add(r)
    await db_session.flush()

    response = await client.get("/api/v1/reports?type=daily")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["type"] == "daily"
