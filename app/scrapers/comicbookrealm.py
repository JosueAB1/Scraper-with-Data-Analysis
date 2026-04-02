"""
app/scrapers/comicbookrealm.py
===============================
Scraper for ComicBookRealm (comicbookrealm.com).

Fix applied:
  - Correct URL: /search/comics/?a=search&series=search&method=all
    (discovered from the 302 redirect logs — the old /search URL was wrong)
  - Added follow_redirects=True via BaseScraper _make_client
  - Inspect real HTML response before parsing to detect structural changes
  - Added explicit logging of how many cards were found per page
  - Multiple fallback selectors for resilience against HTML changes

Known issue: HTML structure changes can break parsers silently.
If 0 results appear, enable DEBUG=true in .env and check redirect logs.
"""

import logging
import re
from typing import Any

from bs4 import BeautifulSoup
from app.scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

BASE_URL = "https://comicbookrealm.com"

# Correct browse URL discovered from redirect chain
# Old (wrong): /search  → 302 → /search/comics/?a=search&series=search&method=all
# New (correct): use the final URL directly
BROWSE_URL = f"{BASE_URL}/search/comics/?a=search&series=search&method=all"

# Publishers to search for — more reliable than letter browsing
PUBLISHERS = [
    "Marvel", "DC Comics", "Image Comics", "Dark Horse",
    "IDW Publishing", "Boom Studios", "Dynamite",
]


class ComicBookRealmScraper(BaseScraper):
    source_name = "comicbookrealm"

    def __init__(self, max_pages: int = 3):
        super().__init__()
        self.max_pages = max_pages

    async def scrape(self) -> list[dict[str, Any]]:
        results: list[dict] = []

        async with self._make_client() as client:
            for publisher in PUBLISHERS:
                for page in range(1, self.max_pages + 1):
                    url = f"{BROWSE_URL}&q={publisher}&page={page}"
                    self.logger.info(
                        f"Scraping publisher='{publisher}' page={page} — {url}"
                    )
                    try:
                        html = await self.fetch_html(client, url)
                        soup = BeautifulSoup(html, "html.parser")

                        # Log page title to confirm we got the right page
                        title_tag = soup.find("title")
                        self.logger.debug(
                            f"Page title: {title_tag.text if title_tag else 'N/A'}"
                        )

                        comics = self._parse_listing(soup)
                        self.logger.info(
                            f"  → {len(comics)} comics found "
                            f"(publisher={publisher}, page={page})"
                        )

                        if not comics:
                            # Log first 500 chars of HTML to diagnose selector issues
                            self.logger.debug(
                                f"Empty result — HTML preview: {html[:500]}"
                            )
                            break

                        results.extend(comics)

                    except Exception as e:
                        self.logger.error(
                            f"Error scraping publisher='{publisher}' page={page}: {e}"
                        )
                        break

        # Deduplicate by cbr_id or title
        seen: set[str] = set()
        unique: list[dict] = []
        for item in results:
            key = item.get("league_id") or item["title"]
            if key not in seen:
                seen.add(key)
                unique.append(item)

        self.logger.info(
            f"ComicBookRealm total: {len(unique)} unique comics from {len(results)} raw"
        )
        return unique

    def _parse_listing(self, soup: BeautifulSoup) -> list[dict[str, Any]]:
        """
        Try multiple selector strategies to find comic cards.
        Logs which selector matched — helps debug HTML changes.
        """
        strategies = [
            ("table.listing tr",      soup.select("table.listing tr")),
            (".comic-item",           soup.select(".comic-item")),
            (".search-result",        soup.select(".search-result")),
            (".result-item",          soup.select(".result-item")),
            ("tr[class*='result']",   soup.select("tr[class*='result']")),
            ("div[class*='comic']",   soup.select("div[class*='comic']")),
        ]

        for name, cards in strategies:
            if cards:
                self.logger.debug(f"Selector matched: '{name}' — {len(cards)} elements")
                results = []
                for card in cards:
                    parsed = self._parse_card(card)
                    if parsed:
                        results.append(parsed)
                return results

        self.logger.warning(
            "No selector matched — HTML structure may have changed. "
            "Enable DEBUG=true in .env for full HTML preview."
        )
        return []

    def _parse_card(self, card) -> dict[str, Any] | None:
        """Extract comic fields from a card element."""
        try:
            # Title — try multiple selectors
            title_tag = (
                card.select_one("a.title")
                or card.select_one(".comic-title")
                or card.select_one("td.title a")
                or card.select_one("h3 a")
                or card.select_one("a[href*='/comic/']")
                or card.select_one("td a")
            )
            title = title_tag.get_text(strip=True) if title_tag else None
            if not title or len(title) < 2:
                return None

            # Source URL + ID
            source_url = None
            cbr_id = None
            link_tag = card.select_one("a[href*='/comic/']") or title_tag
            if link_tag:
                href = link_tag.get("href", "")
                source_url = (
                    href if href.startswith("http")
                    else f"{BASE_URL}{href}"
                )
                m = re.search(r"/comic/(\d+)", href)
                if m:
                    cbr_id = m.group(1)

            # Publisher
            pub_tag = (
                card.select_one(".publisher")
                or card.select_one("td.publisher")
                or card.select_one("[class*='publisher']")
            )
            publisher = pub_tag.get_text(strip=True) if pub_tag else None

            # Cover image
            img_tag = card.select_one("img")
            cover_url = None
            if img_tag:
                cover_url = (
                    img_tag.get("src")
                    or img_tag.get("data-src")
                    or img_tag.get("data-lazy")
                )
                if cover_url and not cover_url.startswith("http"):
                    cover_url = f"{BASE_URL}{cover_url}"

            # Issue number
            issue_tag = card.select_one(".issue, .issue-number, td.issue")
            issue_number = issue_tag.get_text(strip=True) if issue_tag else None

            # Year
            year_tag = card.select_one(".year, td.year, .date")
            publish_date = year_tag.get_text(strip=True) if year_tag else None

            return {
                "league_id": cbr_id,
                "comic_vine_id": None,
                "title": title,
                "issue_number": issue_number,
                "publisher": publisher,
                "description": None,
                "cover_url": cover_url,
                "genres": "",
                "characters": "",
                "publish_date": publish_date,
                "source": "comicbookrealm",
                "source_url": source_url,
                "rating": None,
            }

        except Exception as e:
            self.logger.debug(f"Card parse error: {e}")
            return None


async def scrape_cbr_comics(max_pages: int = 3) -> list[dict]:
    return await ComicBookRealmScraper(max_pages=max_pages).run()