"""
app/schemas/book_schema.py
===========================
Pydantic schemas for the Books domain.
Separated from comic_schema.py so each domain owns its contracts.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class BookResponse(BaseModel):
    id: int
    open_library_id: Optional[str] = None
    title: str
    author: Optional[str] = None
    description: Optional[str] = None
    cover_url: Optional[str] = None
    genres: List[str] = []
    language: Optional[str] = None
    publish_year: Optional[int] = None
    page_count: Optional[int] = None
    publisher: Optional[str] = None
    source_url: Optional[str] = None
    isbn: Optional[str] = None
    scraped_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_with_genres(cls, obj) -> "BookResponse":
        data = {c.name: getattr(obj, c.name) for c in obj.__table__.columns}
        data["genres"] = obj.genres_list()
        return cls(**data)


class BookListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    results: List[BookResponse]