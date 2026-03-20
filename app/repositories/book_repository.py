"""
app/repositories/book_repository.py
=====================================
Repository pattern: encapsulates ALL database queries for books.

Why repositories?
  - Routes and services never write raw SQL / ORM queries.
  - Queries are testable in isolation (just mock the repo).
  - Swapping the data store (e.g. PostgreSQL → MongoDB) only
    requires changes here, not scattered across the codebase.
"""

import logging
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.book import Book

logger = logging.getLogger(__name__)


class BookRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Read ──────────────────────────────────────────────────────────────────

    async def get_by_id(self, book_id: int) -> Optional[Book]:
        return await self.db.get(Book, book_id)

    async def get_by_open_library_id(self, ol_id: str) -> Optional[Book]:
        result = await self.db.execute(
            select(Book).where(Book.open_library_id == ol_id)
        )
        return result.scalar_one_or_none()

    async def get_by_title(self, title: str) -> Optional[Book]:
        result = await self.db.execute(
            select(Book).where(Book.title == title)
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        title: Optional[str] = None,
        author: Optional[str] = None,
        genre: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Book], int]:
        """
        Returns (items, total_count) applying optional filters and pagination.
        """
        stmt = select(Book)

        if title:
            stmt = stmt.where(Book.title.ilike(f"%{title}%"))
        if author:
            stmt = stmt.where(Book.author.ilike(f"%{author}%"))
        if genre:
            stmt = stmt.where(Book.genres.ilike(f"%{genre}%"))

        # Total count before pagination
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total: int = (await self.db.execute(count_stmt)).scalar_one()

        # Paginate
        offset = (page - 1) * page_size
        stmt = stmt.order_by(Book.title).offset(offset).limit(page_size)
        rows = (await self.db.execute(stmt)).scalars().all()

        return list(rows), total

    # ── Write ─────────────────────────────────────────────────────────────────

    async def create(self, data: dict) -> Book:
        book = Book(**{k: v for k, v in data.items() if hasattr(Book, k)})
        self.db.add(book)
        await self.db.commit()
        await self.db.refresh(book)
        return book

    async def update(self, book: Book, data: dict) -> Book:
        for key, value in data.items():
            if hasattr(book, key):
                setattr(book, key, value)
        await self.db.commit()
        await self.db.refresh(book)
        return book

    async def upsert(self, data: dict) -> Book:
        """
        Insert or update a book.
        Matches by open_library_id first, then falls back to title.
        """
        ol_id = data.get("open_library_id")
        existing = None

        if ol_id:
            existing = await self.get_by_open_library_id(ol_id)
        if not existing:
            existing = await self.get_by_title(data.get("title", ""))

        if existing:
            return await self.update(existing, data)
        return await self.create(data)