"""
Comic database model.
Maps to the `comics` table in PostgreSQL.

Updated fields (Abril 2026):
  - writer, artist        — from Kaggle dataset columns Writer/Artist
  - language              — from Country of Origin / Language
  - age_rating            — from Age Rating column
  - format                — from Format column (Single Issue, Trade Paperback, etc.)
  - awards                — from Awards column
  - volume_count          — from Volume Count column
  - status                — from Status column (Ongoing, Completed, etc.)
"""

from datetime import datetime
from sqlalchemy import String, Text, DateTime, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Comic(Base):
    __tablename__ = "comics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # ── External identifiers ──────────────────────────────────────────────────
    comic_vine_id: Mapped[str | None] = mapped_column(String(64), unique=True, index=True)
    league_id: Mapped[str | None] = mapped_column(String(64), index=True)

    # ── Core fields ───────────────────────────────────────────────────────────
    title: Mapped[str] = mapped_column(String(512), index=True)
    issue_number: Mapped[str | None] = mapped_column(String(32))
    publisher: Mapped[str | None] = mapped_column(String(256), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    cover_url: Mapped[str | None] = mapped_column(String(512))
    genres: Mapped[str | None] = mapped_column(Text)
    characters: Mapped[str | None] = mapped_column(Text)
    publish_date: Mapped[str | None] = mapped_column(String(32))
    source: Mapped[str | None] = mapped_column(String(64))
    source_url: Mapped[str | None] = mapped_column(String(512))
    rating: Mapped[float | None] = mapped_column(Float)

    # ── New fields from Kaggle dataset ────────────────────────────────────────
    writer: Mapped[str | None] = mapped_column(String(256))
    artist: Mapped[str | None] = mapped_column(String(256))
    language: Mapped[str | None] = mapped_column(String(64))
    age_rating: Mapped[str | None] = mapped_column(String(64))
    format: Mapped[str | None] = mapped_column(String(128))
    awards: Mapped[str | None] = mapped_column(Text)
    volume_count: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str | None] = mapped_column(String(64))

    # ── Audit ─────────────────────────────────────────────────────────────────
    scraped_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def genres_list(self) -> list[str]:
        if not self.genres:
            return []
        return [g.strip() for g in self.genres.split(",")]