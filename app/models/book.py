"""
Book database model.
Maps to the `books` table in PostgreSQL.

Fix applied:
  - genres changed from String(512) to Text — Open Library returns
    very long genre strings that exceed 512 characters
  - publisher changed from String(256) to Text for same reason
"""

from datetime import datetime
from sqlalchemy import String, Text, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Book(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # ── Identifiers ───────────────────────────────────────────────────────────
    open_library_id: Mapped[str | None] = mapped_column(String(64), unique=True, index=True)
    isbn: Mapped[str | None] = mapped_column(String(20), index=True)

    # ── Core fields ───────────────────────────────────────────────────────────
    title: Mapped[str] = mapped_column(String(512), index=True)
    author: Mapped[str | None] = mapped_column(String(256))
    description: Mapped[str | None] = mapped_column(Text)
    cover_url: Mapped[str | None] = mapped_column(String(512))
    genres: Mapped[str | None] = mapped_column(Text)        # Text — can exceed 512 chars
    language: Mapped[str | None] = mapped_column(String(16))
    publish_year: Mapped[int | None] = mapped_column(Integer)
    page_count: Mapped[int | None] = mapped_column(Integer)
    publisher: Mapped[str | None] = mapped_column(Text)     # Text — multiple publishers
    source_url: Mapped[str | None] = mapped_column(String(512))

    # ── Audit ─────────────────────────────────────────────────────────────────
    scraped_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def genres_list(self) -> list[str]:
        if not self.genres:
            return []
        return [g.strip() for g in self.genres.split(",")]