"""
app/scrapers/base_scraper.py
=============================
Abstract base class for all scrapers.

Why a base class?
  - Enforces a consistent interface: every scraper exposes `scrape()`.
  - Centralizes shared logic: HTTP client creation, retry, delay, logging.
  - New scrapers only override `scrape()` — no boilerplate to copy.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; ComicsBooksAPIBot/1.0; "
        "+https://github.com/yourusername/comics-books-api)"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


class BaseScraper(ABC):
    """
    All scrapers inherit from this class.

    Subclass usage:
        class MyNewScraper(BaseScraper):
            source_name = "my_source"

            async def scrape(self) -> list[dict]:
                data = await self.fetch("https://example.com/api")
                return [self._parse(item) for item in data["results"]]
    """

    source_name: str = "unknown"

    def __init__(self):
        self.logger = logging.getLogger(
            f"{__name__}.{self.__class__.__name__}"
        )

    # ── HTTP helpers ──────────────────────────────────────────────────────────

    def _make_client(self, extra_headers: dict | None = None) -> httpx.AsyncClient:
        headers = {**DEFAULT_HEADERS, **(extra_headers or {})}
        return httpx.AsyncClient(headers=headers)

    async def fetch(
        self,
        client: httpx.AsyncClient,
        url: str,
        params: dict | None = None,
        headers: dict | None = None,
    ) -> dict[str, Any]:
        """
        GET `url` with retry + polite delay.
        Raises on final failure so callers can log and skip.
        """
        last_exc: Exception | None = None

        for attempt in range(settings.SCRAPER_MAX_RETRIES):
            try:
                resp = await client.get(
                    url,
                    params=params,
                    headers=headers,
                    timeout=20.0,
                )
                resp.raise_for_status()
                await asyncio.sleep(settings.SCRAPER_DELAY_SECONDS)
                return resp.json()

            except httpx.HTTPStatusError as e:
                self.logger.warning(
                    f"[{self.source_name}] HTTP {e.response.status_code} "
                    f"on {url} (attempt {attempt + 1}/{settings.SCRAPER_MAX_RETRIES})"
                )
                last_exc = e
                if e.response.status_code in (401, 403, 404):
                    break   # No point retrying auth / not-found errors

            except httpx.RequestError as e:
                self.logger.warning(
                    f"[{self.source_name}] Request error on {url}: {e} "
                    f"(attempt {attempt + 1}/{settings.SCRAPER_MAX_RETRIES})"
                )
                last_exc = e

            await asyncio.sleep(2 ** attempt)   # exponential back-off

        raise last_exc or RuntimeError(f"Failed to fetch {url}")

    async def fetch_html(
        self,
        client: httpx.AsyncClient,
        url: str,
    ) -> str:
        """Fetch a page and return raw HTML text (for BeautifulSoup scrapers)."""
        last_exc: Exception | None = None

        for attempt in range(settings.SCRAPER_MAX_RETRIES):
            try:
                resp = await client.get(url, timeout=20.0)
                resp.raise_for_status()
                await asyncio.sleep(settings.SCRAPER_DELAY_SECONDS)
                return resp.text
            except (httpx.HTTPStatusError, httpx.RequestError) as e:
                self.logger.warning(
                    f"[{self.source_name}] Error fetching HTML {url}: {e} "
                    f"(attempt {attempt + 1})"
                )
                last_exc = e
            await asyncio.sleep(2 ** attempt)

        raise last_exc or RuntimeError(f"Failed to fetch HTML {url}")

    # ── Interface ─────────────────────────────────────────────────────────────

    @abstractmethod
    async def scrape(self) -> list[dict[str, Any]]:
        """
        Run the scraper and return a list of raw dicts.
        Each dict must be compatible with the Book or Comic model fields.
        """
        ...

    async def run(self) -> list[dict[str, Any]]:
        """
        Public entry point. Wraps `scrape()` with top-level error handling
        so a failing scraper never crashes the whole scheduler job.
        """
        self.logger.info(f"[{self.source_name}] Starting scrape …")
        try:
            results = await self.scrape()
            self.logger.info(
                f"[{self.source_name}] Finished — {len(results)} items collected."
            )
            return results
        except Exception as e:
            self.logger.error(
                f"[{self.source_name}] Scrape failed with unhandled error: {e}",
                exc_info=True,
            )
            return []