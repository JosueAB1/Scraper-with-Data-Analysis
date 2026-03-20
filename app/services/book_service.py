"""
app/services/book_service.py
=============================
Business logic for books.

The service layer sits between routes and the repository:
  Route → Service → Repository → DB

Responsibilities:
  - Orchestrate calls to the repository
  - Apply business rules (e.g. validation beyond Pydantic)
  - Transform data between API schemas and domain models
  - This is where you'd add caching, notifications, etc. later
"""

import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.book_repository import BookRepository
from app.schemas.book_schema import BookResponse, BookListResponse

logger = logging.getLogger(__name__)


class BookService:
    def __init__(self, db: AsyncSession):
        self.repo = BookRepository(db)

    async def get_book(self, book_id: int) -> Optional[BookResponse]:
        book = await self.repo.get_by_id(book_id)
        if not book:
            return None
        return BookResponse.from_orm_with_genres(book)

    async def list_books(
        self,
        title: Optional[str] = None,
        author: Optional[str] = None,
        genre: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> BookListResponse:
        books, total = await self.repo.list(
            title=title,
            author=author,
            genre=genre,
            page=page,
            page_size=page_size,
        )
        return BookListResponse(
            total=total,
            page=page,
            page_size=page_size,
            results=[BookResponse.from_orm_with_genres(b) for b in books],
        )

    async def upsert_bulk(self, items: list[dict]) -> int:
        """Upsert a list of scraped book dicts. Returns count of saved records."""
        saved = 0
        for item in items:
            try:
                await self.repo.upsert(item)
                saved += 1
            except Exception as e:
                logger.error(f"Failed upserting book '{item.get('title')}': {e}")
        logger.info(f"BookService: upserted {saved}/{len(items)} books")
        return saved