"""Tests for Paper API endpoints."""

import pytest


@pytest.mark.asyncio
async def test_get_papers_empty(client):
    """GET /papers returns empty list when no papers exist."""
    response = await client.get("/api/v1/papers")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []


@pytest.mark.asyncio
async def test_get_papers_with_data(client, seeded_papers):
    """GET /papers returns seeded papers."""
    response = await client.get("/api/v1/papers")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3


@pytest.mark.asyncio
async def test_get_papers_filter_by_source(client, seeded_papers):
    """GET /papers?source=arxiv filters correctly."""
    response = await client.get("/api/v1/papers?source=arxiv")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2


@pytest.mark.asyncio
async def test_get_paper_by_id_found(client, seeded_papers):
    """GET /papers/{id} returns paper detail."""
    response = await client.get("/api/v1/papers/paper-1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "paper-1"
    assert data["title"] == "A Novel Object Detection Method"
    assert data["source"] == "arxiv"
    assert len(data["categories"]) == 1
    assert data["categories"][0]["name"] == "Object Detection"


@pytest.mark.asyncio
async def test_get_paper_by_id_not_found(client):
    """GET /papers/{id} returns 404 for unknown id."""
    response = await client.get("/api/v1/papers/nonexistent")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_put_paper_tags(client, seeded_papers, seeded_tags):
    """PUT /papers/{id}/tags replaces tags on a paper."""
    response = await client.put(
        "/api/v1/papers/paper-1/tags",
        json={"tag_ids": ["tag-1", "tag-2"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["paper_id"] == "paper-1"
    assert len(data["tags"]) == 2
    tag_names = {t["name"] for t in data["tags"]}
    assert tag_names == {"Important", "To Read"}


@pytest.mark.asyncio
async def test_put_paper_tags_invalid_paper(client, seeded_tags):
    """PUT /papers/{id}/tags returns 404 for unknown paper."""
    response = await client.put(
        "/api/v1/papers/nonexistent/tags",
        json={"tag_ids": ["tag-1"]},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_put_paper_tags_invalid_tag(client, seeded_papers):
    """PUT /papers/{id}/tags returns 422 if tag does not exist."""
    response = await client.put(
        "/api/v1/papers/paper-1/tags",
        json={"tag_ids": ["nonexistent-tag"]},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_paper_detail_includes_authors(client, seeded_papers):
    """GET /papers/{id} returns paper with abstract and empty author list."""
    response = await client.get("/api/v1/papers/paper-1")
    assert response.status_code == 200
    data = response.json()
    assert "abstract" in data
    assert "authors" in data
    assert isinstance(data["authors"], list)
    assert "versions" in data
    assert isinstance(data["versions"], list)
