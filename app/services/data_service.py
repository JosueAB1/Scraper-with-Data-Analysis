"""
app/services/data_service.py
=============================
Top-level orchestrator: runs all scrapers and delegates persistence
to BookService and ComicService.

This is the only file that knows about ALL scrapers.
Individual services only know about their own domain.
"""

import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.scrapers.open_library import scrape_books
from app.scrapers.comic_vine import scrape_comics
from app.scrapers.league_of_comic_geeks import scrape_league_comics
from app.services.book_service import BookService
from app.services.comic_service import ComicService

logger = logging.getLogger(__name__)


async def run_full_scrape(db: AsyncSession) -> dict:
    """
    Execute all scrapers and persist results.
    Returns a summary dict with counts per source.
    """
    summary: dict[str, int] = {}

    book_service  = BookService(db)
    comic_service = ComicService(db)

    # ── Books ──────────────────────────────────────────────────────────────
    logger.info("[ 1/3 ] Scraping Open Library …")
    books = await scrape_books(limit_per_genre=50)
    summary["open_library_books"] = await book_service.upsert_bulk(books)

    # ── Comics — Comic Vine ────────────────────────────────────────────────
    logger.info("[ 2/3 ] Scraping Comic Vine …")
    cv_comics = await scrape_comics(limit=200)
    summary["comic_vine_issues"] = await comic_service.upsert_bulk(cv_comics)

    # ── Comics — League of Comic Geeks ─────────────────────────────────────
    logger.info("[ 3/3 ] Scraping League of Comic Geeks …")
    league_comics = await scrape_league_comics(pages=3)
    summary["league_comics"] = await comic_service.upsert_bulk(league_comics)

    logger.info(f"Full scrape complete — summary: {summary}")
    return summary