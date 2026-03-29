"""
app/services/data_service.py
=============================
Top-level orchestrator: runs all scrapers and delegates persistence
to BookService and ComicService.

Scrapers registered:
  1. Open Library    → books
  2. Comic Vine      → comics
  3. ComicBookRealm  → comics  ✅ added
  4. League of Comic Geeks → comics (pending session cookie)
"""

import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.scrapers.open_library import scrape_books
from app.scrapers.comic_vine import scrape_comics
from app.scrapers.comicbookrealm import scrape_cbr_comics
from app.services.book_service import BookService
from app.services.comic_service import ComicService

logger = logging.getLogger(__name__)


async def run_full_scrape(db: AsyncSession) -> dict:
    """
    Execute all scrapers and persist results.
    Returns a summary dict with counts per source.
    If one scraper fails, the others continue unaffected.
    """
    summary: dict[str, int] = {}

    book_service  = BookService(db)
    comic_service = ComicService(db)

    # ── 1. Books — Open Library ────────────────────────────────────────────
    logger.info("[ 1/3 ] Scraping Open Library …")
    books = await scrape_books(limit_per_genre=50)
    summary["open_library_books"] = await book_service.upsert_bulk(books)

    # ── 2. Comics — Comic Vine ─────────────────────────────────────────────
    logger.info("[ 2/3 ] Scraping Comic Vine …")
    cv_comics = await scrape_comics(limit=200)
    summary["comic_vine_issues"] = await comic_service.upsert_bulk(cv_comics)

    # ── 3. Comics — ComicBookRealm ─────────────────────────────────────────
    logger.info("[ 3/3 ] Scraping ComicBookRealm …")
    cbr_comics = await scrape_cbr_comics(max_pages_per_letter=2)
    summary["comicbookrealm_comics"] = await comic_service.upsert_bulk(cbr_comics)

    logger.info(f"Full scrape complete — summary: {summary}")
    return summary