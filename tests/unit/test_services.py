"""
tests/unit/test_services.py
============================
Unit tests for BookService and ComicService.
Repositories are mocked — no DB required.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.book_service import BookService
from app.services.comic_service import ComicService


# ── BookService ───────────────────────────────────────────────────────────────

@pytest.fixture
def mock_db():
    return AsyncMock(spec=AsyncSession)


@pytest.mark.asyncio
async def test_book_service_get_book_not_found(mock_db):
    service = BookService(mock_db)
    service.repo.get_by_id = AsyncMock(return_value=None)

    result = await service.get_book(999)
    assert result is None


@pytest.mark.asyncio
async def test_book_service_upsert_bulk_handles_errors(mock_db):
    service = BookService(mock_db)

    async def failing_upsert(data):
        raise Exception("DB error")

    service.repo.upsert = failing_upsert

    items = [{"title": "Book A"}, {"title": "Book B"}]
    saved = await service.upsert_bulk(items)
    assert saved == 0   # all failed, none saved


@pytest.mark.asyncio
async def test_book_service_list_books_empty(mock_db):
    service = BookService(mock_db)
    service.repo.list = AsyncMock(return_value=([], 0))

    result = await service.list_books(page=1, page_size=20)
    assert result.total == 0
    assert result.results == []
    assert result.page == 1


# ── ComicService ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_comic_service_get_comic_not_found(mock_db):
    service = ComicService(mock_db)
    service.repo.get_by_id = AsyncMock(return_value=None)

    result = await service.get_comic(999)
    assert result is None


@pytest.mark.asyncio
async def test_comic_service_list_empty(mock_db):
    service = ComicService(mock_db)
    service.repo.list = AsyncMock(return_value=([], 0))

    result = await service.list_comics()
    assert result.total == 0
    assert result.results == []