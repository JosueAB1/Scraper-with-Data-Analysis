"""
app/api/routes/books.py
========================
Routes delegate ALL logic to BookService — zero raw DB queries here.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_api_key
from app.services.book_service import BookService
from app.schemas.book_schema import BookResponse, BookListResponse

router = APIRouter()


@router.get(
    "/books",
    response_model=BookListResponse,
    summary="List books",
    description="Paginated list of books. Filter by title, author, or genre.",
)
async def list_books(
    title: Optional[str] = Query(None, description="Partial title search"),
    author: Optional[str] = Query(None, description="Partial author search"),
    genre: Optional[str] = Query(None, description="Filter by genre (e.g. 'fantasy')"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _: str = Depends(require_api_key),
    db: AsyncSession = Depends(get_db),
):
    service = BookService(db)
    return await service.list_books(
        title=title, author=author, genre=genre, page=page, page_size=page_size
    )


@router.get(
    "/books/{book_id}",
    response_model=BookResponse,
    summary="Get book by ID",
)
async def get_book(
    book_id: int,
    _: str = Depends(require_api_key),
    db: AsyncSession = Depends(get_db),
):
    service = BookService(db)
    book = await service.get_book(book_id)
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found.")
    return book