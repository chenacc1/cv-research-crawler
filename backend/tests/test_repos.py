"""Tests for Repo API endpoints."""

import pytest


@pytest.mark.asyncio
async def test_get_repos_empty(client):
    """GET /repos returns empty list when no repos exist."""
    response = await client.get("/api/v1/repos")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []


@pytest.mark.asyncio
async def test_get_repos_with_data(client, seeded_repos):
    """GET /repos returns seeded repos."""
    response = await client.get("/api/v1/repos")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_get_repos_sort_by_stars(client, seeded_repos):
    """GET /repos?sort=stars returns repos sorted by stars desc."""
    response = await client.get("/api/v1/repos?sort=-stars")
    assert response.status_code == 200
    data = response.json()
    items = data["items"]
    # First should have more stars (1500 > 800)
    assert items[0]["stars"] >= items[1]["stars"] if len(items) > 1 else True


@pytest.mark.asyncio
async def test_get_repo_by_id_found(client, seeded_repos):
    """GET /repos/{id} returns repo detail."""
    response = await client.get("/api/v1/repos/repo-1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "repo-1"
    assert data["full_name"] == "test/detection-lib"
    assert data["stars"] == 1500
    assert data["language"] == "Python"
    assert "computer-vision" in data["topics"]


@pytest.mark.asyncio
async def test_get_repo_by_id_not_found(client):
    """GET /repos/{id} returns 404 for unknown id."""
    response = await client.get("/api/v1/repos/nonexistent")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_put_repo_tags(client, seeded_repos, seeded_tags):
    """PUT /repos/{id}/tags replaces tags on a repo."""
    response = await client.put(
        "/api/v1/repos/repo-1/tags",
        json={"tag_ids": ["tag-1"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["repo_id"] == "repo-1"
    assert len(data["tags"]) == 1
    assert data["tags"][0]["name"] == "Important"


@pytest.mark.asyncio
async def test_put_repo_tags_invalid_repo(client, seeded_tags):
    """PUT /repos/{id}/tags returns 404 for unknown repo."""
    response = await client.put(
        "/api/v1/repos/nonexistent/tags",
        json={"tag_ids": ["tag-1"]},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_repos_filter_by_language(client, seeded_repos):
    """GET /repos?language=Python filters by language."""
    response = await client.get("/api/v1/repos?language=Python")
    assert response.status_code == 200
    data = response.json()
    for item in data["items"]:
        assert item["language"] == "Python"
