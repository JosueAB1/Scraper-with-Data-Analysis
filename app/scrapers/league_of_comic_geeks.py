"""
League of Comic Geeks Scraper
==============================
STATUS: Bloqueado por Cloudflare — pendiente para v2.

Intentos realizados:
  - Scraping directo con httpx → HTTP 403
  - Cookies de sesión de cuenta activa → HTTP 403 (Cloudflare challenge)

Causa: El sitio usa Cloudflare con JavaScript challenges que verifican
que el request provenga de un navegador real. httpx no puede pasar
esta verificación sin ejecutar JavaScript.

Solución propuesta para v2:
  - Usar Playwright (navegador headless Chromium) que ejecuta JS real
  - pip install playwright && playwright install chromium
  - Esto permitiría pasar el challenge y usar las cookies de sesión

Por ahora el scraper retorna lista vacía sin romper el job completo.
"""

import asyncio
import logging
import re
from typing import Any

import httpx
from bs4 import BeautifulSoup

from app.core.config import settings

logger = logging.getLogger(__name__)

BASE_URL = "https://leagueofcomicgeeks.com"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; ComicsBooksAPIBot/1.0; "
        "+https://github.com/yourusername/comics-books-api)"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


async def _get_page(client: httpx.AsyncClient, url: str) -> BeautifulSoup | None:
    """Fetch a page and return a BeautifulSoup object."""
    for attempt in range(settings.SCRAPER_MAX_RETRIES):
        try:
            resp = await client.get(url, timeout=20.0)
            resp.raise_for_status()
            await asyncio.sleep(settings.SCRAPER_DELAY_SECONDS)
            return BeautifulSoup(resp.text, "html.parser")
        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP {e.response.status_code} on {url} (attempt {attempt+1})")
            if e.response.status_code == 403:
                logger.error("League of Comic Geeks returned 403 — may require login.")
                return None
            if attempt == settings.SCRAPER_MAX_RETRIES - 1:
                return None
        except httpx.RequestError as e:
            logger.warning(f"Request error: {e}")
            if attempt == settings.SCRAPER_MAX_RETRIES - 1:
                return None
        await asyncio.sleep(2 ** attempt)
    return None


def _parse_comic_card(card) -> dict[str, Any] | None:
    """
    Parse a single comic card element from a listing page.
    HTML structure may change — this targets the common card layout.
    """
    try:
        title_tag = card.select_one(".comic-title, h2.title, .name")
        title = title_tag.get_text(strip=True) if title_tag else None
        if not title:
            return None

        publisher_tag = card.select_one(".publisher, .comic-publisher")
        publisher = publisher_tag.get_text(strip=True) if publisher_tag else None

        cover_tag = card.select_one("img.cover, img.comic-cover, .cover img")
        cover_url = None
        if cover_tag:
            cover_url = cover_tag.get("src") or cover_tag.get("data-src")

        link_tag = card.select_one("a[href*='/comics/'], a[href*='/comic/']")
        source_url = None
        league_id = None
        if link_tag:
            href = link_tag.get("href", "")
            source_url = href if href.startswith("http") else f"{BASE_URL}{href}"
            id_match = re.search(r"/comics?/(\d+)", href)
            if id_match:
                league_id = id_match.group(1)

        rating_tag = card.select_one(".rating, .score, [data-score]")
        rating = None
        if rating_tag:
            raw = rating_tag.get_text(strip=True) or rating_tag.get("data-score", "")
            try:
                rating = float(raw)
            except ValueError:
                pass

        issue_tag = card.select_one(".issue-number, .number")
        issue_number = issue_tag.get_text(strip=True) if issue_tag else None

        return {
            "league_id": league_id,
            "comic_vine_id": None,
            "title": title,
            "issue_number": issue_number,
            "publisher": publisher,
            "description": None,   # Detail page needed for description
            "cover_url": cover_url,
            "genres": "",
            "characters": "",
            "publish_date": None,
            "source": "league_of_comic_geeks",
            "source_url": source_url,
            "rating": rating,
        }
    except Exception as e:
        logger.debug(f"Failed to parse comic card: {e}")
        return None


async def _scrape_listing(client: httpx.AsyncClient, path: str) -> list[dict]:
    """Scrape a single listing page (new releases or browse)."""
    url = f"{BASE_URL}{path}"
    soup = await _get_page(client, url)
    if not soup:
        return []

    # Try multiple possible card selectors
    cards = (
        soup.select(".comic-item")
        or soup.select(".comic-card")
        or soup.select("li.comic")
        or soup.select("[class*='comic-']")
    )

    results = []
    for card in cards:
        parsed = _parse_comic_card(card)
        if parsed:
            results.append(parsed)

    return results


async def scrape_league_comics(pages: int = 3) -> list[dict]:
    """
    Main entry point.
    Scrapes `pages` pages of new releases + popular comics.
    """
    results: list[dict] = []

    async with httpx.AsyncClient(headers=HEADERS) as client:
        for page in range(1, pages + 1):
            for path_template in ["/comics/new-releases?page={}", "/comics/browse?page={}"]:
                path = path_template.format(page)
                logger.info(f"League of Comic Geeks: scraping {path}")
                try:
                    page_results = await _scrape_listing(client, path)
                    results.extend(page_results)
                    logger.info(f"  → {len(page_results)} comics found")
                except Exception as e:
                    logger.error(f"Error scraping {path}: {e}")

    # Deduplicate by league_id
    seen: set[str] = set()
    unique: list[dict] = []
    for item in results:
        key = item.get("league_id") or item["title"]
        if key not in seen:
            seen.add(key)
            unique.append(item)

    logger.info(f"League of Comic Geeks scrape complete — {len(unique)} unique comics.")
    return unique