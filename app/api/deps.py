"""
app/api/deps.py
===============
FastAPI dependency functions used across all routers.

Centralizing deps here means:
  - Routes import from ONE place (not scattered imports).
  - Easy to mock in tests by overriding app.dependency_overrides.
  - Adding new shared deps (e.g. current_user) has a clear home.
"""

from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.core.security import require_api_key  # re-exported for convenience

__all__ = ["get_db", "require_api_key"]


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Yield a DB session for the duration of a request, then close it.

    Usage in a route:
        async def my_route(db: AsyncSession = Depends(get_db)):
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()