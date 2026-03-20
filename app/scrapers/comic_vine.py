"""
Comic Vine Scraper
==================
Uses the official Comic Vine REST API (requires a free API key):
  https://comicvine.gamespot.com/api/

Flow:
  1. Query /issues endpoint sorted by date_added (newest first).
  2. For each issue, extract title, publisher, cover, genres, characters.
  3. Upsert into `comics` table.

Rate limit: 200 requests/hour on the free tier.
We stay well within limits by adding a delay between requests.
"""

import asyncio
import logging
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

BASE_URL = "https://comicvine.gamespot.com/api"


async def _fetch(client: httpx.AsyncClient, endpoint: str, params: dict) -> dict:
    """GET request against Comic Vine API with retries."""
    params.setdefault("api_key", settings.COMIC_VINE_API_KEY)
    params.setdefault("format", "json")

    url = f"{BASE_URL}/{endpoint}"
    for attempt in range(settings.SCRAPER_MAX_RETRIES):
        try:
            resp = await client.get(url, params=params, timeout=20.0)
            resp.raise_for_status()
            await asyncio.sleep(settings.SCRAPER_DELAY_SECONDS)
            return resp.json()
        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP {e.response.status_code} fetching {endpoint} (attempt {attempt+1})")
            if attempt == settings.SCRAPER_MAX_RETRIES - 1:
                raise
        except httpx.RequestError as e:
            logger.warning(f"Request error on {endpoint}: {e}")
            if attempt == settings.SCRAPER_MAX_RETRIES - 1:
                raise
        await asyncio.sleep(2 ** attempt)
    return {}


def _parse_issue(issue: dict) -> dict[str, Any]:
    """Map a Comic Vine issue dict to our internal schema."""
    volume = issue.get("volume") or {}
    publisher = volume.get("name", "")

    characters = issue.get("character_credits") or []
    char_names = ", ".join(c["name"] for c in characters[:15])

    cover_date = issue.get("cover_date") or ""

    return {
        "comic_vine_id": str(issue.get("id", "")),
        "title": issue.get("name") or volume.get("name", "Unknown"),
        "issue_number": str(issue.get("issue_number") or ""),
        "publisher": publisher,
        "description": _strip_html(issue.get("description") or issue.get("deck") or ""),
        "cover_url": issue.get("image", {}).get("medium_url"),
        "genres": "",           # Comic Vine issues don't have genre tags; see volume genres below
        "characters": char_names,
        "publish_date": cover_date,
        "source": "comic_vine",
        "source_url": issue.get("site_detail_url"),
        "rating": None,
    }


def _strip_html(text: str) -> str:
    """Very light HTML tag removal — avoids importing BeautifulSoup for a simple task."""
    import re
    return re.sub(r"<[^>]+>", "", text).strip()


async def scrape_comics(limit: int = 200) -> list[dict]:
    """
    Main entry point.
    Returns parsed comic dicts ready for upserting.
    Requires COMIC_VINE_API_KEY set in .env.
    """
    if not settings.COMIC_VINE_API_KEY:
        logger.warning("COMIC_VINE_API_KEY not set — skipping Comic Vine scraper.")
        return []

    results: list[dict] = []
    offset = 0
    page_size = 100  # max allowed by API

    async with httpx.AsyncClient(
        headers={"User-Agent": "ComicsBooksAPI/1.0 (portfolio project)"}
    ) as client:
        while len(results) < limit:
            logger.info(f"Comic Vine: fetching issues offset={offset}")
            try:
                data = await _fetch(
                    client,
                    "issues",
                    params={
                        "field_list": (
                            "id,name,issue_number,volume,cover_date,"
                            "image,description,deck,character_credits,site_detail_url"
                        ),
                        "sort": "date_added:desc",
                        "limit": min(page_size, limit - len(results)),
                        "offset": offset,
                    },
                )
                issues = data.get("results", [])
                if not issues:
                    break

                for issue in issues:
                    results.append(_parse_issue(issue))

                offset += page_size
                if offset >= data.get("number_of_total_results", 0):
                    break
            except Exception as e:
                logger.error(f"Comic Vine scrape error at offset {offset}: {e}")
                break

    logger.info(f"Comic Vine scrape complete — {len(results)} issues collected.")
    return results