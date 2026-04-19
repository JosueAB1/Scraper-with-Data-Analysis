# 📚 Comics & Books API

A production-grade REST API built with **FastAPI** and deployed on **Railway** that aggregates comic and book data from multiple sources via web scraping and public datasets.

[![CI](https://github.com/JosueAB1/Scraper-with-Data-Analysis/actions/workflows/ci.yml/badge.svg)](https://github.com/JosueAB1/Scraper-with-Data-Analysis/actions)
[![Python](https://img.shields.io/badge/python-3.12-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)](https://fastapi.tiangolo.com)
[![Railway](https://img.shields.io/badge/deployed-Railway-purple)](https://railway.app)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🌐 Live Demo

| URL | Description |
|-----|-------------|
| `https://tu-proyecto.railway.app/docs` | Interactive Swagger UI |
| `https://tu-proyecto.railway.app/health` | Health check |

> All endpoints require an `X-API-Key` header. Contact the author for a demo key.

---

## 📖 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Data Sources](#-data-sources)
- [Quick Start](#-quick-start)
- [API Reference](#-api-reference)
- [Running Tests](#-running-tests)
- [Deployment](#-deployment)
- [Known Issues](#-known-issues)

---

## ✨ Features

- **REST API** with full OpenAPI / Swagger documentation
- **API Key authentication** via `X-API-Key` header
- **10,450+ records** — 450 books + 10,000 comics
- **Search** by title and author (case-insensitive partial match)
- **Filter** by genre, publisher, and data source
- **Pagination** on all list endpoints (max 100 per page)
- **Async scrapers** for Open Library with weekly scheduling via APScheduler
- **PostgreSQL** with SQLAlchemy 2.x async ORM
- **Upsert logic** — re-running scrapers is always safe
- **26 tests** — unit + integration with GitHub Actions CI
- **Deployed on Railway** with automatic deploys on push

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────┐
│                   FastAPI App                        │
│  /api/v1/books   /api/v1/comics   /api/v1/auth      │
└───────────────────────┬─────────────────────────────┘
                        │ Repository Pattern
                        ▼
               ┌────────────────┐
               │  PostgreSQL    │
               │  books table   │
               │  comics table  │
               └───────┬────────┘
                       │ upsert
                       ▼
         ┌─────────────────────────┐
         │     Scrapers            │
         │  Open Library API       │
         │  Comic Vine API         │
         │  Kaggle CSV (pandas)    │
         └─────────────────────────┘
```

**Layer breakdown:**

| Layer | Files | Responsibility |
|-------|-------|----------------|
| Routes | `api/routes/*.py` | HTTP — receive requests |
| Dependencies | `api/deps.py` | Centralized `get_db`, auth |
| Services | `services/*_service.py` | Business logic per domain |
| Repositories | `repositories/*.py` | All DB queries |
| Models | `models/book.py`, `models/comic.py` | ORM table structure |
| Schemas | `schemas/*_schema.py` | Pydantic validation |
| BaseScraper | `scrapers/base_scraper.py` | HTTP, retry, redirects |

---

## 🌐 Data Sources

| Source | Type | Records | Status |
|--------|------|---------|--------|
| [Open Library](https://openlibrary.org/developers/api) | Public API | 450 books | ✅ Active |
| [Kaggle — Comic Books Dataset](https://kaggle.com/datasets/rudrakumargupta/comic-books-dataset-10000-entries) | CSV Import | 10,000 comics | ✅ Imported |
| [Comic Vine](https://comicvine.gamespot.com/api/) | Public API | Pending | ⚠️ Diagnosing |
| Marvel API | Official API | — | ❌ Deprecated by Marvel (2025) |
| League of Comic Geeks | HTML Scraping | — | ❌ Cloudflare protected |
| ComicBookRealm | HTML Scraping | — | ❌ Returns marketplace, not DB |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- PostgreSQL 14+

### Setup

```bash
git clone https://github.com/JosueAB1/Scraper-with-Data-Analysis.git
cd Scraper-with-Data-Analysis

python -m venv venv
source venv/bin/activate        # Mac/Linux
# .\venv\Scripts\Activate.ps1   # Windows

pip install -r requirements.txt
cp .env.example .env            # Fill in your values
```

### Environment variables

```env
DATABASE_URL=postgresql+asyncpg://postgres:yourpassword@localhost:5432/comics_books_db
API_KEYS=generate-with-secrets.token_hex(32)
COMIC_VINE_API_KEY=your-free-key-from-comicvine.gamespot.com
DEBUG=false
```

### Run locally

```bash
# Create DB
psql -U postgres -c "CREATE DATABASE comics_books_db;"

# Apply migrations
alembic upgrade head

# Start API
uvicorn app.main:app --reload
# → http://localhost:8000/docs

# Run scrapers (separate terminal)
python scripts/run_scraper.py
```

---

## 📡 API Reference

All endpoints require `X-API-Key` header.

### Books

```http
GET /api/v1/books
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `title` | string | Partial title search |
| `author` | string | Partial author search |
| `genre` | string | Filter by genre |
| `page` | int | Page number (default: 1) |
| `page_size` | int | Results per page (1–100, default: 20) |

```bash
# Example
curl -H "X-API-Key: your-key" \
  "https://tu-proyecto.railway.app/api/v1/books?genre=fantasy&page=1"
```

```json
{
  "total": 48,
  "page": 1,
  "page_size": 20,
  "results": [
    {
      "id": 12,
      "title": "A Wizard of Earthsea",
      "author": "Ursula K. Le Guin",
      "genres": ["fantasy", "young adult"],
      "publish_year": 1968,
      "scraped_at": "2026-04-02T23:36:43"
    }
  ]
}
```

### Comics

```http
GET /api/v1/comics
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `title` | string | Partial title search |
| `genre` | string | Filter by genre |
| `publisher` | string | Filter by publisher |
| `source` | string | `kaggle_dataset` or `comic_vine` |
| `page` | int | Page number |
| `page_size` | int | Results per page (1–100) |

```bash
# Marvel comics
curl -H "X-API-Key: your-key" \
  "https://tu-proyecto.railway.app/api/v1/comics?publisher=Marvel Comics"

# Horror genre
curl -H "X-API-Key: your-key" \
  "https://tu-proyecto.railway.app/api/v1/comics?genre=Horror"
```

### Auth

```bash
curl -H "X-API-Key: your-key" \
  "https://tu-proyecto.railway.app/api/v1/auth/verify"
# → {"status": "authenticated", "key_prefix": "your-key..."}
```

---

## 🧪 Running Tests

```bash
pytest -v                        # All 26 tests
pytest tests/unit/ -v            # Unit tests only
pytest tests/integration/ -v     # Integration tests only
```

Tests are fully isolated — no real network or database required.

---

## 🚢 Deployment

Deployed on **Railway** with automatic deploys from the `develop` branch.

### Stack
- **Runtime**: Docker with `python:3.12-slim`
- **Database**: Railway PostgreSQL (managed)
- **CI/CD**: GitHub Actions → Railway auto-deploy

### Branch strategy

```
main      ← production (protected — PR + CI required)
develop   ← integration (auto-deploys to Railway)
feature/* ← individual features/fixes
```

### Environment variables on Railway

| Variable | Notes |
|----------|-------|
| `DATABASE_URL` | Auto-generated by Railway — do not set manually |
| `API_KEYS` | Production key — different from local |
| `COMIC_VINE_API_KEY` | Same as local |
| `DEBUG` | Always `false` in production |

---

## ⚠️ Known Issues

### Comic Vine — empty response body
The API key is valid (returns 200 with correct JSON in direct tests) but the scraper receives an empty body (`char 0`) during scheduled runs. Likely rate limiting. Under investigation.

### League of Comic Geeks — Cloudflare
Protected by Cloudflare JavaScript challenges. Static scraping with `httpx` returns HTTP 403 regardless of session cookies. Planned fix: Playwright headless browser in v2.

### ComicBookRealm — marketplace content
The search endpoint returns auction marketplace listings (with prices and end dates), not a comic database. Investigated and discarded as a data source.

### Git history — pre-April 2026
Commits before April 2026 use simple messages (`Edit file.py`). Conventional Commits were adopted from that date forward as part of the project's development process.

---

## 🛠 Tech Stack

| Tool | Version | Purpose |
|------|---------|---------|
| FastAPI | 0.115.6 | Web framework + OpenAPI docs |
| SQLAlchemy | 2.0.36 | Async ORM |
| asyncpg | 0.30.0 | PostgreSQL async driver |
| Alembic | 1.14.0 | DB migrations |
| Pydantic v2 | 2.10.3 | Data validation |
| httpx | 0.28.1 | Async HTTP client |
| BeautifulSoup4 | 4.12.3 | HTML parsing |
| APScheduler | 3.10.4 | Weekly cron scheduling |
| pandas | Latest | Kaggle CSV import |
| pytest | 8.3.4 | Testing framework |
| Railway | — | Cloud deployment |

---

## 📄 License

MIT License