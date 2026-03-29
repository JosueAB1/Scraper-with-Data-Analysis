"""
Comic Vine Scraper
==================
Official REST API (free key required): https://comicvine.gamespot.com/api/
Inherits HTTP + retry logic from BaseScraper.

Fixes applied:
  - Added User-Agent: Mozilla/5.0 to bypass 403
  - Added follow_redirects=True to handle 301
"""

import logging
import re
from typing import Any

import httpx

from app.scrapers.base_scraper import BaseScraper
from app.core.config import settings

logger = logging.getLogger(__name__)
BASE_URL = "https://comicvine.gamespot.com/api"


class ComicVineScraper(BaseScraper):
    source_name = "comic_vine"

    def __init__(self, limit: int = 200):
        super().__init__()
        self.limit = limit

    async def scrape(self) -> list[dict[str, Any]]:
        if not settings.COMIC_VINE_API_KEY:
            self.logger.warning("COMIC_VINE_API_KEY not set — skipping.")
            return []

        results: list[dict] = []
        offset = 0
        page_size = 100

        async with httpx.AsyncClient(
            headers={"User-Agent": "Mozilla/5.0"},
            follow_redirects=True,
        ) as client:
            while len(results) < self.limit:
                try:
                    data = await self.fetch(
                        client,
                        f"{BASE_URL}/issues",
                        params={
                            "api_key": settings.COMIC_VINE_API_KEY,
                            "format": "json",
                            "field_list": (
                                "id,name,issue_number,volume,cover_date,"
                                "image,description,deck,character_credits,site_detail_url"
                            ),
                            "sort": "date_added:desc",
                            "limit": min(page_size, self.limit - len(results)),
                            "offset": offset,
                        },
                    )
                    issues = data.get("results", [])
                    if not issues:
                        break
                    for issue in issues:
                        results.append(self._parse_issue(issue))
                    offset += page_size
                    if offset >= data.get("number_of_total_results", 0):
                        break
                except Exception as e:
                    self.logger.error(f"Error at offset {offset}: {e}")
                    break

        return results

    @staticmethod
    def _parse_issue(issue: dict) -> dict[str, Any]:
        volume = issue.get("volume") or {}
        characters = issue.get("character_credits") or []
        char_names = ", ".join(c["name"] for c in characters[:15])
        desc = issue.get("description") or issue.get("deck") or ""

        return {
            "comic_vine_id": str(issue.get("id", "")),
            "title": issue.get("name") or volume.get("name", "Unknown"),
            "issue_number": str(issue.get("issue_number") or ""),
            "publisher": volume.get("name", ""),
            "description": re.sub(r"<[^>]+>", "", desc).strip(),
            "cover_url": (issue.get("image") or {}).get("medium_url"),
            "genres": "",
            "characters": char_names,
            "publish_date": issue.get("cover_date") or "",
            "source": "comic_vine",
            "source_url": issue.get("site_detail_url"),
            "rating": None,
        }


# ── Convenience function (used by data_service + scheduler) ──────────────────

async def scrape_comics(limit: int = 200) -> list[dict]:
    return await ComicVineScraper(limit=limit).run()