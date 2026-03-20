"""
app/db/database.py
==================
Owns:
  - Async SQLAlchemy engine
  - DeclarativeBase (all models inherit from here)
  - init_db() — creates tables on startup (dev/test convenience)

Does NOT own session creation → see session.py
"""

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,     # SQL query logging only in DEBUG mode
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)


class Base(DeclarativeBase):
    """All ORM models inherit from this base."""
    pass


async def init_db() -> None:
    """
    Create all tables (idempotent).
    In production, prefer Alembic migrations instead.
    Useful for tests and first-run local dev.
    """
    from app.models import book, comic  # noqa: F401 — registers models
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)