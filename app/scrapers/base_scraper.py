"""
app/scrapers/base_scraper.py
=============================
Abstract base class for all scrapers.

Fixes applied:
  - _make_client: follow_redirects=True always (fixes 301/302)
  - fetch(): uses resp.content + chardet/fallback encoding instead of resp.json()
    This fixes UnicodeDecodeError when Comic Vine returns non-UTF8 bytes
  - fetch_html(): same redirect fix
  - run(): always logs full traceback for diagnosis
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}


def _safe_json(resp: httpx.Response) -> dict:
    """
    Parse response as JSON safely.
    Falls back through multiple encodings before raising.
    Fixes UnicodeDecodeError when server returns non-UTF8 bytes.
    """
    # Try encodings in order of likelihood
    for encoding in ("utf-8", "latin-1", "utf-8-sig", "cp1252"):
        try:
            return json.loads(resp.content.decode(encoding))
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue

    # Last resort: decode with replacement characters
    text = resp.content.decode("utf-8", errors="replace")
    return json.loads(text)


class BaseScraper(ABC):
    source_name: str = "unknown"

    def __init__(self):
        self.logger = logging.getLogger(
            f"{__name__}.{self.__class__.__name__}"
        )

    def _make_client(self, extra_headers: dict | None = None) -> httpx.AsyncClient:
        """
        Always creates client with follow_redirects=True.
        Fixes 301/302 issues that previously caused empty results.
        """
        headers = {**DEFAULT_HEADERS, **(extra_headers or {})}
        return httpx.AsyncClient(
            headers=headers,
            follow_redirects=True,
            timeout=20.0,
        )

    async def fetch(
        self,
        client: httpx.AsyncClient,
        url: str,
        params: dict | None = None,
        headers: dict | None = None,
    ) -> dict[str, Any]:
        """
        GET url, follow redirects, return parsed JSON dict.
        Uses _safe_json() to handle non-UTF8 responses.
        """
        last_exc: Exception | None = None

        for attempt in range(settings.SCRAPER_MAX_RETRIES):
            try:
                resp = await client.get(url, params=params, headers=headers)

                if str(resp.url) != url:
                    self.logger.debug(
                        f"[{self.source_name}] Redirected: {url} → {resp.url}"
                    )

                resp.raise_for_status()
                await asyncio.sleep(settings.SCRAPER_DELAY_SECONDS)

                # Use encoding-safe parser instead of resp.json()
                return _safe_json(resp)

            except httpx.HTTPStatusError as e:
                self.logger.warning(
                    f"[{self.source_name}] HTTP {e.response.status_code} on {url} "
                    f"(attempt {attempt + 1}/{settings.SCRAPER_MAX_RETRIES})"
                )
                last_exc = e
                if e.response.status_code in (401, 403, 404):
                    break

            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                self.logger.error(
                    f"[{self.source_name}] Failed to decode response from {url}: {e}"
                )
                last_exc = e
                break  # No point retrying a decode error

            except httpx.RequestError as e:
                self.logger.warning(
                    f"[{self.source_name}] Request error on {url}: {e} "
                    f"(attempt {attempt + 1}/{settings.SCRAPER_MAX_RETRIES})"
                )
                last_exc = e

            await asyncio.sleep(2 ** attempt)

        raise last_exc or RuntimeError(f"Failed to fetch {url}")

    async def fetch_html(
        self,
        client: httpx.AsyncClient,
        url: str,
    ) -> str:
        """Fetch a page and return raw HTML with redirect following."""
        last_exc: Exception | None = None

        for attempt in range(settings.SCRAPER_MAX_RETRIES):
            try:
                resp = await client.get(url)

                if str(resp.url) != url:
                    self.logger.debug(
                        f"[{self.source_name}] HTML redirect: {url} → {resp.url}"
                    )

                resp.raise_for_status()
                await asyncio.sleep(settings.SCRAPER_DELAY_SECONDS)
                return resp.text

            except httpx.HTTPStatusError as e:
                self.logger.warning(
                    f"[{self.source_name}] HTTP {e.response.status_code} "
                    f"fetching {url} (attempt {attempt + 1})"
                )
                last_exc = e
                if e.response.status_code in (401, 403, 404):
                    self.logger.error(
                        f"[{self.source_name}] {e.response.status_code} — stopping retries."
                    )
                    break

            except httpx.RequestError as e:
                self.logger.warning(
                    f"[{self.source_name}] Request error: {e} (attempt {attempt + 1})"
                )
                last_exc = e

            await asyncio.sleep(2 ** attempt)

        raise last_exc or RuntimeError(f"Failed to fetch HTML {url}")

    @abstractmethod
    async def scrape(self) -> list[dict[str, Any]]:
        ...

    async def run(self) -> list[dict[str, Any]]:
        """Runs scrape() safely — returns [] on any error."""
        self.logger.info(f"[{self.source_name}] Starting scrape …")
        try:
            results = await self.scrape()
            self.logger.info(
                f"[{self.source_name}] Finished — {len(results)} items collected."
            )
            return results
        except Exception as e:
            self.logger.error(
                f"[{self.source_name}] Scrape failed: {e}",
                exc_info=True,
            )
            return []