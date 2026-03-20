"""
app/db/session.py
=================
Async session factory, separated from the engine/Base declarations.

Why separate from database.py?
  - database.py owns the engine + Base (infrastructure concerns).
  - session.py owns session creation (usage concern).
  - This makes it easy to swap session config in tests without
    touching engine setup.
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from app.db.database import engine

AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)