"""
app/services/comic_service.py
==============================
Business logic for comics. Mirrors BookService structure.
"""

import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.comic_repository import ComicRepository
from app.schemas.comic_schema import ComicResponse, ComicListResponse

logger = logging.getLogger(__name__)


class ComicService:
    def __init__(self, db: AsyncSession):
        self.repo = ComicRepository(db)

    async def get_comic(self, comic_id: int) -> Optional[ComicResponse]:
        comic = await self.repo.get_by_id(comic_id)
        if not comic:
            return None
        return ComicResponse.from_orm_with_genres(comic)

    async def list_comics(
        self,
        title: Optional[str] = None,
        genre: Optional[str] = None,
        publisher: Optional[str] = None,
        source: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> ComicListResponse:
        comics, total = await self.repo.list(
            title=title,
            genre=genre,
            publisher=publisher,
            source=source,
            page=page,
            page_size=page_size,
        )
        return ComicListResponse(
            total=total,
            page=page,
            page_size=page_size,
            results=[ComicResponse.from_orm_with_genres(c) for c in comics],
        )

    async def upsert_bulk(self, items: list[dict]) -> int:
        saved = 0
        for item in items:
            try:
                await self.repo.upsert(item)
                saved += 1
            except Exception as e:
                logger.error(f"Failed upserting comic '{item.get('title')}': {e}")
        logger.info(f"ComicService: upserted {saved}/{len(items)} comics")
        return saved