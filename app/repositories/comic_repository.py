"""
app/repositories/comic_repository.py
======================================
Repository pattern for comics. Mirrors BookRepository structure.
"""

import logging
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.comic import Comic

logger = logging.getLogger(__name__)


class ComicRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Read ──────────────────────────────────────────────────────────────────

    async def get_by_id(self, comic_id: int) -> Optional[Comic]:
        return await self.db.get(Comic, comic_id)

    async def get_by_comic_vine_id(self, cv_id: str) -> Optional[Comic]:
        result = await self.db.execute(
            select(Comic).where(Comic.comic_vine_id == cv_id)
        )
        return result.scalar_one_or_none()

    async def get_by_league_id(self, league_id: str) -> Optional[Comic]:
        result = await self.db.execute(
            select(Comic).where(Comic.league_id == league_id)
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        title: Optional[str] = None,
        genre: Optional[str] = None,
        publisher: Optional[str] = None,
        source: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Comic], int]:
        stmt = select(Comic)

        if title:
            stmt = stmt.where(Comic.title.ilike(f"%{title}%"))
        if genre:
            stmt = stmt.where(Comic.genres.ilike(f"%{genre}%"))
        if publisher:
            stmt = stmt.where(Comic.publisher.ilike(f"%{publisher}%"))
        if source:
            stmt = stmt.where(Comic.source == source)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total: int = (await self.db.execute(count_stmt)).scalar_one()

        offset = (page - 1) * page_size
        stmt = stmt.order_by(Comic.title).offset(offset).limit(page_size)
        rows = (await self.db.execute(stmt)).scalars().all()

        return list(rows), total

    # ── Write ─────────────────────────────────────────────────────────────────

    async def create(self, data: dict) -> Comic:
        comic = Comic(**{k: v for k, v in data.items() if hasattr(Comic, k)})
        self.db.add(comic)
        await self.db.commit()
        await self.db.refresh(comic)
        return comic

    async def update(self, comic: Comic, data: dict) -> Comic:
        for key, value in data.items():
            if hasattr(comic, key):
                setattr(comic, key, value)
        await self.db.commit()
        await self.db.refresh(comic)
        return comic

    async def upsert(self, data: dict) -> Comic:
        """
        Insert or update a comic.
        Matches by comic_vine_id, then league_id, then title.
        """
        existing = None
        cv_id = data.get("comic_vine_id")
        lg_id = data.get("league_id")

        if cv_id:
            existing = await self.get_by_comic_vine_id(cv_id)
        if not existing and lg_id:
            existing = await self.get_by_league_id(lg_id)

        if existing:
            return await self.update(existing, data)
        return await self.create(data)