"""
app/api/routes/comics.py
=========================
Routes delegate ALL logic to ComicService.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_api_key
from app.services.comic_service import ComicService
from app.schemas.comic_schema import ComicResponse, ComicListResponse

router = APIRouter()


@router.get(
    "/comics",
    response_model=ComicListResponse,
    summary="List comics",
    description="Paginated list of comics. Filter by title, genre, publisher, or source.",
)
async def list_comics(
    title: Optional[str] = Query(None, description="Partial title search"),
    genre: Optional[str] = Query(None, description="Filter by genre"),
    publisher: Optional[str] = Query(None, description="Filter by publisher (e.g. 'Marvel')"),
    source: Optional[str] = Query(None, description="comic_vine | league_of_comic_geeks"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _: str = Depends(require_api_key),
    db: AsyncSession = Depends(get_db),
):
    service = ComicService(db)
    return await service.list_comics(
        title=title, genre=genre, publisher=publisher,
        source=source, page=page, page_size=page_size,
    )


@router.get(
    "/comics/{comic_id}",
    response_model=ComicResponse,
    summary="Get comic by ID",
)
async def get_comic(
    comic_id: int,
    _: str = Depends(require_api_key),
    db: AsyncSession = Depends(get_db),
):
    service = ComicService(db)
    comic = await service.get_comic(comic_id)
    if not comic:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comic not found.")
    return comic