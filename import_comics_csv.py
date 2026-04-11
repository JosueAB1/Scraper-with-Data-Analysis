"""
import_comics_csv.py
=====================
Importa el dataset de Kaggle (comics.csv) a la tabla comics de PostgreSQL.

Uso:
    python import_comics_csv.py

Prerequisitos:
    pip install pandas asyncpg sqlalchemy
    El archivo comics.csv debe estar en la misma carpeta que este script.
    Las migraciones de Alembic deben estar aplicadas (alembic upgrade head).

Columnas del CSV mapeadas:
    comic_id          → league_id
    Title             → title
    Studio/Publisher  → publisher
    Genre             → genres
    Release Year      → publish_date
    Rating (out of 10)→ rating
    Writer            → writer
    Artist            → artist
    Language          → language
    Age Rating        → age_rating
    Format            → format
    Awards            → awards
    Volume Count      → volume_count
    Status            → status
"""

import asyncio
import logging
import sys
import os
from datetime import datetime
from pathlib import Path

# Permite correr desde cualquier carpeta del proyecto
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


async def import_csv():
    try:
        import pandas as pd
    except ImportError:
        logger.error("pandas no instalado. Corre: pip install pandas")
        return

    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from sqlalchemy import text
    from dotenv import load_dotenv

    load_dotenv()
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/comics_books_db"
    )

    # ── Cargar CSV ────────────────────────────────────────────────────────────
    csv_path = Path(__file__).parent / "comics.csv"
    if not csv_path.exists():
        logger.error(f"Archivo no encontrado: {csv_path}")
        logger.error("Asegurate de que comics.csv este en la misma carpeta que este script.")
        return

    logger.info(f"Cargando {csv_path} ...")
    df = pd.read_csv(csv_path, encoding="utf-8", on_bad_lines="skip")
    logger.info(f"CSV cargado: {len(df)} filas, columnas: {list(df.columns)}")

    # ── Limpiar y mapear columnas ─────────────────────────────────────────────
    def clean_str(val) -> str | None:
        if pd.isna(val) or str(val).strip() in ("", "nan", "N/A", "None"):
            return None
        return str(val).strip()

    def clean_float(val) -> float | None:
        try:
            f = float(val)
            return f if not pd.isna(f) else None
        except (ValueError, TypeError):
            return None

    def clean_int(val) -> int | None:
        try:
            i = int(float(val))
            return i
        except (ValueError, TypeError):
            return None

    records = []
    for _, row in df.iterrows():
        record = {
            "league_id":    clean_str(row.get("comic_id")),
            "comic_vine_id": None,
            "title":        clean_str(row.get("Title")) or "Unknown",
            "publisher":    clean_str(row.get("Studio/Publisher")),
            "genres":       clean_str(row.get("Genre")),
            "publish_date": clean_str(row.get("Release Year")),
            "rating":       clean_float(row.get("Rating (out of 10)")),
            "writer":       clean_str(row.get("Writer")),
            "artist":       clean_str(row.get("Artist")),
            "language":     clean_str(row.get("Language")),
            "age_rating":   clean_str(row.get("Age Rating")),
            "format":       clean_str(row.get("Format")),
            "awards":       clean_str(row.get("Awards")),
            "volume_count": clean_int(row.get("Volume Count")),
            "status":       clean_str(row.get("Status")),
            # Fields not in CSV — set defaults
            "issue_number": None,
            "description":  None,
            "cover_url":    None,
            "characters":   None,
            "source":       "kaggle_dataset",
            "source_url":   None,
            "scraped_at":   datetime.utcnow(),
        }
        records.append(record)

    logger.info(f"Registros preparados: {len(records)}")

    # ── Insertar en PostgreSQL ────────────────────────────────────────────────
    engine = create_async_engine(DATABASE_URL, echo=False)
    AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    inserted = 0
    skipped  = 0
    errors   = 0

    async with AsyncSessionLocal() as session:
        for i, record in enumerate(records, 1):
            try:
                # Upsert: si ya existe por league_id, actualizar; si no, insertar
                if record["league_id"]:
                    existing = await session.execute(
                        text("SELECT id FROM comics WHERE league_id = :lid"),
                        {"lid": record["league_id"]}
                    )
                    row = existing.fetchone()
                    if row:
                        skipped += 1
                        continue

                await session.execute(
                    text("""
                        INSERT INTO comics (
                            league_id, comic_vine_id, title, publisher, genres,
                            publish_date, rating, writer, artist, language,
                            age_rating, format, awards, volume_count, status,
                            issue_number, description, cover_url, characters,
                            source, source_url, scraped_at
                        ) VALUES (
                            :league_id, :comic_vine_id, :title, :publisher, :genres,
                            :publish_date, :rating, :writer, :artist, :language,
                            :age_rating, :format, :awards, :volume_count, :status,
                            :issue_number, :description, :cover_url, :characters,
                            :source, :source_url, :scraped_at
                        )
                    """),
                    record
                )
                inserted += 1

                # Commit cada 500 registros para no saturar la transacción
                if inserted % 500 == 0:
                    await session.commit()
                    logger.info(f"  {inserted} registros insertados...")

            except Exception as e:
                errors += 1
                logger.warning(f"Error en fila {i} ({record.get('title')}): {e}")
                await session.rollback()

        await session.commit()

    await engine.dispose()

    logger.info("=" * 50)
    logger.info(f"Importacion completa:")
    logger.info(f"  Insertados:  {inserted}")
    logger.info(f"  Ya existian: {skipped}")
    logger.info(f"  Errores:     {errors}")
    logger.info(f"  Total CSV:   {len(records)}")
    logger.info("=" * 50)

    # Verificar total en DB
    engine2 = create_async_engine(DATABASE_URL, echo=False)
    async with engine2.connect() as conn:
        result = await conn.execute(text("SELECT COUNT(*) FROM comics"))
        total = result.scalar()
        logger.info(f"Total comics en DB ahora: {total}")
    await engine2.dispose()


if __name__ == "__main__":
    asyncio.run(import_csv())