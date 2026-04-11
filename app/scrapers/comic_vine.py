"""
Comic Vine Scraper
==================
Official REST API: https://comicvine.gamespot.com/api/

Fix applied:
  - Override fetch() to use resp.json() directly instead of _safe_json()
    The API returns valid UTF-8 JSON — _safe_json was overcomplicating it
    and failing on empty responses
  - Added explicit check for empty response body before parsing
  - Added status_detail validation — if API returns error, log and stop
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

    async def _fetch_cv(self, client: httpx.AsyncClient, params: dict) -> dict | None:
        """
        Comic Vine specific fetch — uses resp.json() directly.
        Returns None if response is empty or not valid JSON.
        """
        import asyncio
        try:
            resp = await client.get(f"{BASE_URL}/issues/", params=params)

            if len(resp.content) == 0:
                self.logger.error("Comic Vine returned empty response body.")
                return None

            resp.raise_for_status()
            await asyncio.sleep(settings.SCRAPER_DELAY_SECONDS)

            data = resp.json()

            status = data.get("status_detail", "")
            if status and status != "OK":
                self.logger.error(f"Comic Vine API error: {status}")
                return None

            return data

        except httpx.HTTPStatusError as e:
            self.logger.error(f"Comic Vine HTTP {e.response.status_code}")
            return None
        except Exception as e:
            self.logger.error(f"Comic Vine fetch error: {e}", exc_info=True)
            return None

    async def scrape(self) -> list[dict[str, Any]]:
        if not settings.COMIC_VINE_API_KEY:
            self.logger.warning("COMIC_VINE_API_KEY not set — skipping.")
            return []

        results: list[dict] = []
        offset = 0
        page_size = 100

        async with self._make_client() as client:
            while len(results) < self.limit:
                self.logger.info(
                    f"Fetching issues offset={offset} "
                    f"(collected {len(results)}/{self.limit})"
                )

                data = await self._fetch_cv(client, params={
                    "api_key": settings.COMIC_VINE_API_KEY,
                    "format": "json",
                    "field_list": (
                        "id,name,issue_number,volume,cover_date,"
                        "image,description,deck,character_credits,site_detail_url"
                    ),
                    "sort": "date_added:desc",
                    "limit": min(page_size, self.limit - len(results)),
                    "offset": offset,
                })

                if data is None:
                    self.logger.error("Stopping Comic Vine scrape — fetch returned None.")
                    break

                total = data.get("number_of_total_results", 0)
                self.logger.info(f"Comic Vine total available: {total}")

                issues = data.get("results", [])
                if not issues:
                    self.logger.info("No more issues — stopping.")
                    break

                for issue in issues:
                    results.append(self._parse_issue(issue))

                offset += page_size
                if offset >= total:
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


async def scrape_comics(limit: int = 200) -> list[dict]:
    return await ComicVineScraper(limit=limit).run()