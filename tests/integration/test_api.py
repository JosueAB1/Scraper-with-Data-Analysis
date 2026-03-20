"""
tests/integration/test_api.py
==============================
Integration tests for the REST API endpoints.
Uses httpx.AsyncClient with ASGI transport — no real server needed.
DB dependency is mocked via FastAPI's dependency_overrides.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.api.deps import get_db

VALID_KEY = "integration-test-key"


@pytest.fixture(autouse=True)
def patch_api_keys(monkeypatch):
    monkeypatch.setattr("app.core.config.settings.API_KEYS", VALID_KEY)


@pytest.fixture
def mock_db():
    db = AsyncMock(spec=AsyncSession)
    app.dependency_overrides[get_db] = lambda: db
    yield db
    app.dependency_overrides.clear()


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c


# ── Health ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_root(client):
    resp = await client.get("/")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.json()["status"] == "ok"


# ── Auth ──────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_missing_key_returns_403(client):
    resp = await client.get("/api/v1/books")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_wrong_key_returns_403(client):
    resp = await client.get("/api/v1/books", headers={"X-API-Key": "wrong"})
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_verify_valid_key(client):
    resp = await client.get(
        "/api/v1/auth/verify", headers={"X-API-Key": VALID_KEY}
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "authenticated"


# ── Books ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_books_empty(client, mock_db):
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_result.scalar_one.return_value = 0
    mock_db.execute.return_value = mock_result

    resp = await client.get("/api/v1/books", headers={"X-API-Key": VALID_KEY})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 0
    assert body["results"] == []
    assert body["page"] == 1


@pytest.mark.asyncio
async def test_list_books_pagination(client, mock_db):
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_result.scalar_one.return_value = 0
    mock_db.execute.return_value = mock_result

    resp = await client.get(
        "/api/v1/books?page=2&page_size=5",
        headers={"X-API-Key": VALID_KEY},
    )
    assert resp.status_code == 200
    assert resp.json()["page"] == 2
    assert resp.json()["page_size"] == 5


@pytest.mark.asyncio
async def test_get_book_not_found(client, mock_db):
    mock_db.get.return_value = None
    resp = await client.get("/api/v1/books/9999", headers={"X-API-Key": VALID_KEY})
    assert resp.status_code == 404


# ── Comics ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_comics_empty(client, mock_db):
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_result.scalar_one.return_value = 0
    mock_db.execute.return_value = mock_result

    resp = await client.get("/api/v1/comics", headers={"X-API-Key": VALID_KEY})
    assert resp.status_code == 200
    assert resp.json()["total"] == 0


@pytest.mark.asyncio
async def test_get_comic_not_found(client, mock_db):
    mock_db.get.return_value = None
    resp = await client.get("/api/v1/comics/9999", headers={"X-API-Key": VALID_KEY})
    assert resp.status_code == 404