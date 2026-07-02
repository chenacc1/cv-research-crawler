"""Tests for Tag CRUD endpoints."""

import pytest


@pytest.mark.asyncio
async def test_get_tags_empty(client):
    """GET /tags returns empty list when no tags exist."""
    response = await client.get("/api/v1/tags")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []


@pytest.mark.asyncio
async def test_get_tags_with_data(client, seeded_tags):
    """GET /tags lists all tags."""
    response = await client.get("/api/v1/tags")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_create_tag(client):
    """POST /tags creates a new tag."""
    response = await client.post(
        "/api/v1/tags",
        json={"name": "New Tag", "color": "#22C55E"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "New Tag"
    assert data["color"] == "#22C55E"
    assert data["paper_count"] == 0
    assert data["repo_count"] == 0


@pytest.mark.asyncio
async def test_create_tag_duplicate_name(client, seeded_tags):
    """POST /tags returns 409 for duplicate name."""
    response = await client.post(
        "/api/v1/tags",
        json={"name": "Important", "color": "#22C55E"},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_create_tag_invalid_color(client):
    """POST /tags returns 422 for invalid color."""
    response = await client.post(
        "/api/v1/tags",
        json={"name": "Bad Color", "color": "#ZZZZZZ"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_tag(client, seeded_tags):
    """PUT /tags/{id} updates a tag."""
    response = await client.put(
        "/api/v1/tags/tag-1",
        json={"name": "Updated Name", "color": "#10B981"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["color"] == "#10B981"


@pytest.mark.asyncio
async def test_update_tag_not_found(client):
    """PUT /tags/{id} returns 404 for unknown id."""
    response = await client.put(
        "/api/v1/tags/nonexistent",
        json={"name": "Test"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_tag_duplicate_name(client, seeded_tags):
    """PUT /tags/{id} returns 409 for name conflict."""
    response = await client.put(
        "/api/v1/tags/tag-1",
        json={"name": "To Read"},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_delete_tag(client, seeded_tags):
    """DELETE /tags/{id} deletes a tag."""
    response = await client.delete("/api/v1/tags/tag-1")
    assert response.status_code == 204

    # Verify it's gone
    response = await client.get("/api/v1/tags")
    data = response.json()
    assert len(data["items"]) == 1


@pytest.mark.asyncio
async def test_delete_tag_not_found(client):
    """DELETE /tags/{id} returns 404 for unknown id."""
    response = await client.delete("/api/v1/tags/nonexistent")
    assert response.status_code == 404
