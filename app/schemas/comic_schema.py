"""
app/schemas/comic_schema.py
============================
Pydantic schemas for the Comics domain.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class ComicResponse(BaseModel):
    id: int
    comic_vine_id: Optional[str] = None
    league_id: Optional[str] = None
    title: str
    issue_number: Optional[str] = None
    publisher: Optional[str] = None
    description: Optional[str] = None
    cover_url: Optional[str] = None
    genres: List[str] = []
    characters: List[str] = []
    publish_date: Optional[str] = None
    source: Optional[str] = None
    source_url: Optional[str] = None
    rating: Optional[float] = None
    scraped_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_with_genres(cls, obj) -> "ComicResponse":
        data = {c.name: getattr(obj, c.name) for c in obj.__table__.columns}
        data["genres"] = obj.genres_list()
        data["characters"] = (
            [c.strip() for c in obj.characters.split(",")]
            if obj.characters else []
        )
        return cls(**data)


class ComicListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    results: List[ComicResponse]