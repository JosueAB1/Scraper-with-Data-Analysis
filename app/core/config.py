"""
Core configuration loaded from environment variables / .env file.
All secrets (DB password, API keys) are read from the environment —
never hardcoded in source code.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # ── General ───────────────────────────────────────────────────────────────
    DEBUG: bool = False

    # ── Database ──────────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/comics_books_db"

    # ── Security ──────────────────────────────────────────────────────────────
    # Comma-separated list stored in .env: API_KEYS=key1,key2
    API_KEYS: str = "change-me-in-env"

    @property
    def valid_api_keys(self) -> List[str]:
        return [k.strip() for k in self.API_KEYS.split(",")]

    # ── CORS ──────────────────────────────────────────────────────────────────
    ALLOWED_ORIGINS: List[str] = ["*"]

    # ── External API keys ─────────────────────────────────────────────────────
    COMIC_VINE_API_KEY: str = ""   # https://comicvine.gamespot.com/api/

    # ── Scraper ───────────────────────────────────────────────────────────────
    SCRAPER_DELAY_SECONDS: float = 1.5   # Polite delay between requests
    SCRAPER_MAX_RETRIES: int = 3

    # ── Scheduler ─────────────────────────────────────────────────────────────
    # Cron expression for weekly scraping (every Monday at 02:00 UTC)
    SCRAPE_CRON: str = "0 2 * * 1"


settings = Settings()