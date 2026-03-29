"""
app/scrapers/comicbookrealm.py
===============================
Scraper for ComicBookRealm (comicbookrealm.com).
Uses HTML scraping with httpx + BeautifulSoup.
Inherits HTTP, retry and delay logic from BaseScraper.

Pages scraped:
  - /search?type=comic&letter=A..Z  (browse by letter)
  - Each comic detail page for description and genre

ComicBookRealm allows public browsing without login.
"""

import logging
import re
from typing import Any

from bs4 import BeautifulSoup
from app.scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

BASE_URL = "https://comicbookrealm.com"

# Browse by first letter of title — covers the full catalog
BROWSE_LETTERS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ") + ["0"]


class ComicBookRealmScraper(BaseScraper):
    source_name = "comicbookrealm"

    def __init__(self, max_pages_per_letter: int = 2):
        super().__init__()
        self.max_pages_per_letter = max_pages_per_letter

    async def scrape(self) -> list[dict[str, Any]]:
        results: list[dict] = []

        async with self._make_client(
            extra_headers={"User-Agent": "Mozilla/5.0"}
        ) as client:
            for letter in BROWSE_LETTERS:
                for page in range(1, self.max_pages_per_letter + 1):
                    url = f"{BASE_URL}/search"
                    self.logger.info(
                        f"Scraping letter={letter} page={page}"
                    )
                    try:
                        html = await self.fetch_html(client, url)
                        soup = BeautifulSoup(html, "html.parser")
                        comics = self._parse_listing(soup)

                        if not comics:
                            break   # No more pages for this letter

                        results.extend(comics)

                    except Exception as e:
                        self.logger.error(
                            f"Error scraping letter={letter} page={page}: {e}"
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

        return unique

    def _parse_listing(self, soup: BeautifulSoup) -> list[dict[str, Any]]:
        """Parse comic cards from a listing/search results page."""
        comics: list[dict] = []

        # ComicBookRealm uses various card layouts — try multiple selectors
        cards = (
            soup.select(".comic-listing .item")
            or soup.select(".search-results .result")
            or soup.select("table.listing tr")
            or soup.select(".comic-item")
            or soup.select("[class*='comic']")
        )

        for card in cards:
            parsed = self._parse_card(card)
            if parsed:
                comics.append(parsed)

        return comics

    def _parse_card(self, card) -> dict[str, Any] | None:
        """Extract fields from a single comic card element."""
        try:
            # Title
            title_tag = (
                card.select_one("a.title")
                or card.select_one(".comic-title")
                or card.select_one("td.title a")
                or card.select_one("h3 a")
                or card.select_one("a[href*='/comic/']")
            )
            title = title_tag.get_text(strip=True) if title_tag else None
            if not title:
                return None

            # Source URL + ID
            source_url = None
            cbr_id = None
            link_tag = card.select_one("a[href*='/comic/']")
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
            issue_number = (
                issue_tag.get_text(strip=True) if issue_tag else None
            )

            # Year / publish date
            year_tag = card.select_one(".year, td.year, .date")
            publish_date = (
                year_tag.get_text(strip=True) if year_tag else None
            )

            return {
                "league_id": cbr_id,        # reusing league_id field for CBR id
                "comic_vine_id": None,
                "title": title,
                "issue_number": issue_number,
                "publisher": publisher,
                "description": None,        # only available on detail page
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


# ── Convenience function ──────────────────────────────────────────────────────

async def scrape_cbr_comics(max_pages_per_letter: int = 2) -> list[dict]:
    return await ComicBookRealmScraper(
        max_pages_per_letter=max_pages_per_letter
    ).run()