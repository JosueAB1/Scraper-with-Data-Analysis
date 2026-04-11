"""
app/scrapers/comicbookrealm.py
===============================
Scraper for ComicBookRealm (comicbookrealm.com).

Investigation findings:
  - /search/comics/?a=search&series=search&method=all&q=Marvel
    returns a MARKETPLACE page (eBay-style listings with prices)
    NOT a comic database — wrong endpoint entirely

  - Correct pages are the series/publisher browse pages:
    /series/publisher/{publisher-slug}
    /report/series/list/{letter}

  Fix: Use the series list pages browsed by first letter.
  URL format: https://comicbookrealm.com/report/series/list/a
  These pages contain actual comic series with title, publisher, year.
"""

import logging
import re
from typing import Any

from bs4 import BeautifulSoup
from app.scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

BASE_URL = "https://comicbookrealm.com"

# Browse series by first letter — these are the real comic database pages
LETTERS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")


class ComicBookRealmScraper(BaseScraper):
    source_name = "comicbookrealm"

    def __init__(self, max_letters: int = 5):
        super().__init__()
        # Limit letters to avoid overloading — covers A-E by default
        self.letters = LETTERS[:max_letters]

    async def scrape(self) -> list[dict[str, Any]]:
        results: list[dict] = []

        async with self._make_client() as client:
            for letter in self.letters:
                url = f"{BASE_URL}/report/series/list/{letter.lower()}"
                self.logger.info(f"Scraping letter={letter} — {url}")
                try:
                    html = await self.fetch_html(client, url)
                    soup = BeautifulSoup(html, "html.parser")

                    # Log page title for confirmation
                    title_tag = soup.find("title")
                    self.logger.debug(
                        f"Page title: {title_tag.text if title_tag else 'N/A'}"
                    )

                    comics = self._parse_series_page(soup, letter)
                    self.logger.info(
                        f"  letter={letter} → {len(comics)} series found"
                    )

                    if not comics:
                        self.logger.debug(
                            f"Empty — HTML preview: {html[:300]}"
                        )

                    results.extend(comics)

                except Exception as e:
                    self.logger.error(f"Error scraping letter={letter}: {e}")

        # Deduplicate by cbr_id or title
        seen: set[str] = set()
        unique: list[dict] = []
        for item in results:
            key = item.get("league_id") or item["title"]
            if key not in seen:
                seen.add(key)
                unique.append(item)

        self.logger.info(
            f"ComicBookRealm total: {len(unique)} unique series"
        )
        return unique

    def _parse_series_page(
        self, soup: BeautifulSoup, letter: str
    ) -> list[dict[str, Any]]:
        """
        Parse the series list page for a given letter.
        Tries multiple selector strategies and logs which one matched.
        """
        strategies = [
            ("table.list tr",          soup.select("table.list tr")),
            ("table tr",               soup.select("table tr")),
            (".series-list li",        soup.select(".series-list li")),
            (".series-item",           soup.select(".series-item")),
            ("tr.row-even, tr.row-odd",soup.select("tr.row-even, tr.row-odd")),
            ("ul.series li",           soup.select("ul.series li")),
            ("div.series",             soup.select("div.series")),
        ]

        for name, cards in strategies:
            if cards:
                self.logger.debug(
                    f"[letter={letter}] Selector '{name}' matched "
                    f"{len(cards)} elements"
                )
                results = []
                for card in cards:
                    parsed = self._parse_card(card)
                    if parsed:
                        results.append(parsed)
                if results:
                    return results

        self.logger.warning(
            f"[letter={letter}] No selector matched — "
            "HTML structure may have changed. Enable DEBUG=true for preview."
        )
        return []

    def _parse_card(self, card) -> dict[str, Any] | None:
        """Extract series info from a table row or list item."""
        try:
            # Find any link — series pages link to /series/ or /comic/
            link_tag = (
                card.select_one("a[href*='/series/']")
                or card.select_one("a[href*='/comic/']")
                or card.select_one("a[href*='/report/']")
                or card.select_one("a")
            )

            if not link_tag:
                return None

            title = link_tag.get_text(strip=True)
            if not title or len(title) < 2:
                return None

            href = link_tag.get("href", "")
            source_url = (
                href if href.startswith("http") else f"{BASE_URL}{href}"
            )

            # Extract ID from URL
            cbr_id = None
            m = re.search(r"/(?:series|comic)/(\d+)", href)
            if m:
                cbr_id = m.group(1)

            # Publisher — often in a second cell or span
            cells = card.select("td")
            publisher = None
            publish_date = None
            if len(cells) >= 2:
                publisher = cells[1].get_text(strip=True) or None
            if len(cells) >= 3:
                publish_date = cells[2].get_text(strip=True) or None

            return {
                "league_id": cbr_id,
                "comic_vine_id": None,
                "title": title,
                "issue_number": None,
                "publisher": publisher,
                "description": None,
                "cover_url": None,
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
    # max_pages reused as max_letters for consistency with data_service
    return await ComicBookRealmScraper(max_letters=max_pages).run()