"""
scripts/run_scraper.py
======================
Standalone runner + weekly APScheduler cron.

Run manually:   python scripts/run_scraper.py
The script:
  1. Runs a full scrape immediately on start.
  2. Schedules subsequent scrapes via cron (default: every Monday 02:00 UTC).
"""

import asyncio
import logging
import sys
import os

# Allow running from repo root: python scripts/run_scraper.py
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings
from app.core.logging import setup_logging
from app.db.database import init_db
from app.db.session import AsyncSessionLocal
from app.services.data_service import run_full_scrape

logger = logging.getLogger(__name__)


async def job():
    """Scheduled job — runs all scrapers and persists data."""
    async with AsyncSessionLocal() as db:
        summary = await run_full_scrape(db)
    logger.info(f"Scrape job complete: {summary}")


async def main():
    setup_logging()
    await init_db()

    # Run immediately on first start
    logger.info("Running initial scrape …")
    await job()

    # Schedule weekly runs
    cron_parts = settings.SCRAPE_CRON.split()
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        job,
        CronTrigger(
            minute=cron_parts[0],
            hour=cron_parts[1],
            day=cron_parts[2],
            month=cron_parts[3],
            day_of_week=cron_parts[4],
        ),
        id="weekly_scrape",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(f"Scheduler active — cron: {settings.SCRAPE_CRON}")

    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("Scheduler stopped.")


if __name__ == "__main__":
    asyncio.run(main())