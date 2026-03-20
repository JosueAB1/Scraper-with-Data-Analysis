"""
Open Library Scraper
====================
Inherits shared HTTP logic from BaseScraper.
Uses the Open Library Search + Works APIs (no key required).
"""

import logging
from typing import Any

from app.scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

BASE_URL = "https://openlibrary.org"
COVER_URL = "https://covers.openlibrary.org/b/id/{cover_id}-M.jpg"

GENRES_TO_SCRAPE = [
    "science fiction", "fantasy", "mystery", "thriller",
    "horror", "romance", "biography", "history", "graphic novel",
]


class OpenLibraryScraper(BaseScraper):
    source_name = "open_library"

    def __init__(self, limit_per_genre: int = 50):
        super().__init__()
        self.limit_per_genre = limit_per_genre

    async def scrape(self) -> list[dict[str, Any]]:
        results: list[dict] = []

        async with self._make_client() as client:
            for genre in GENRES_TO_SCRAPE:
                self.logger.info(f"Scraping genre: {genre}")
                try:
                    data = await self.fetch(
                        client,
                        f"{BASE_URL}/search.json",
                        params={
                            "subject": genre,
                            "limit": self.limit_per_genre,
                            "fields": (
                                "key,title,author_name,cover_i,subject,"
                                "first_publish_year,number_of_pages_median,"
                                "publisher,isbn,language"
                            ),
                        },
                    )
                    for doc in data.get("docs", []):
                        work_key = doc.get("key", "")
                        description = await self._get_description(client, work_key)
                        results.append(self._parse_book(doc, description))
                except Exception as e:
                    self.logger.error(f"Failed on genre '{genre}': {e}")

        return results

    async def _get_description(self, client, work_key: str) -> str:
        if not work_key:
            return ""
        try:
            data = await self.fetch(client, f"{BASE_URL}{work_key}.json")
            desc = data.get("description", "")
            return desc.get("value", "") if isinstance(desc, dict) else str(desc)
        except Exception:
            return ""

    @staticmethod
    def _parse_book(doc: dict, description: str) -> dict[str, Any]:
        cover_id = doc.get("cover_i")
        return {
            "open_library_id": doc.get("key", "").replace("/works/", ""),
            "title": doc.get("title", "Unknown"),
            "author": ", ".join(doc.get("author_name", [])),
            "description": description or None,
            "cover_url": COVER_URL.format(cover_id=cover_id) if cover_id else None,
            "genres": ", ".join((doc.get("subject") or [])[:10]),
            "language": (doc.get("language") or [""])[0],
            "publish_year": doc.get("first_publish_year"),
            "page_count": doc.get("number_of_pages_median"),
            "publisher": ", ".join((doc.get("publisher") or [])[:3]),
            "isbn": (doc.get("isbn") or [None])[0],
            "source_url": f"{BASE_URL}{doc.get('key', '')}",
        }


async def scrape_books(limit_per_genre: int = 50) -> list[dict]:
    return await OpenLibraryScraper(limit_per_genre=limit_per_genre).run()