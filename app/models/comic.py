"""
Comic database model.
Maps to the `comics` table in PostgreSQL.
Data sourced from Comic Vine and League of Comic Geeks.
"""

from datetime import datetime
from sqlalchemy import String, Text, DateTime, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Comic(Base):
    __tablename__ = "comics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # ── Identifiers ───────────────────────────────────────────────────────────
    comic_vine_id: Mapped[str | None] = mapped_column(String(64), unique=True, index=True)
    league_id: Mapped[str | None] = mapped_column(String(64), index=True)

    # ── Core fields ───────────────────────────────────────────────────────────
    title: Mapped[str] = mapped_column(String(512), index=True)
    issue_number: Mapped[str | None] = mapped_column(String(32))
    publisher: Mapped[str | None] = mapped_column(String(256), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    cover_url: Mapped[str | None] = mapped_column(String(512))
    genres: Mapped[str | None] = mapped_column(String(512))  # comma-separated
    characters: Mapped[str | None] = mapped_column(Text)     # comma-separated
    publish_date: Mapped[str | None] = mapped_column(String(32))
    source: Mapped[str | None] = mapped_column(String(64))   # "comic_vine" | "league"
    source_url: Mapped[str | None] = mapped_column(String(512))
    rating: Mapped[float | None] = mapped_column(Float)

    # ── Audit ─────────────────────────────────────────────────────────────────
    scraped_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def genres_list(self) -> list[str]:
        if not self.genres:
            return []
        return [g.strip() for g in self.genres.split(",")]