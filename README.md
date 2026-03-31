# 📚 Comics & Books API

A production-grade REST API built with **FastAPI** that aggregates comic and book data from multiple sources via web scraping and public APIs. Designed as a portfolio project showcasing async Python, PostgreSQL, scheduled scrapers, and clean API design.

[![CI](https://github.com/yourusername/comics-books-api/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/comics-books-api/actions)
[![Python](https://img.shields.io/badge/python-3.12-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📖 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Data Sources](#-data-sources)
- [Project Structure](#-project-structure)
- [Quick Start](#-quick-start)
- [Configuration](#-configuration)
- [API Reference](#-api-reference)
- [Running the Scraper](#-running-the-scraper)
- [Running Tests](#-running-tests)
- [Known Limitations](#-known-limitations)
- [Deployment](#-deployment)

---

## ✨ Features

- **REST API** with full OpenAPI / Swagger documentation (`/docs`)
- **API Key authentication** via `X-API-Key` header
- **Search** by title and author (case-insensitive partial match)
- **Filter** by genre, publisher, and data source
- **Pagination** on all list endpoints
- **Async scrapers** for 3 active data sources
- **Weekly scheduled scraping** via APScheduler (cron)
- **PostgreSQL** storage with SQLAlchemy 2.x async ORM
- **Repository pattern** — all DB queries encapsulated
- **Upsert logic** — re-running the scraper is always safe
- **pytest test suite** — unit + integration, 11 tests passing
- **GitHub Actions CI** on every push

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────┐
│                        FastAPI App                       │
│  /api/v1/books    /api/v1/comics    /api/v1/auth/verify  │
└───────────────────────────┬─────────────────────────────┘
                            │ SQLAlchemy async
                            ▼
                    ┌───────────────┐
                    │  PostgreSQL   │
                    │  books table  │
                    │  comics table │
                    └───────┬───────┘
                            │ upsert
                            ▼
              ┌─────────────────────────────┐
              │        run_scraper.py        │
              │  (APScheduler — weekly cron) │
              └──────┬──────────┬────────────┘
                     │          │
          ┌──────────▼──┐  ┌────▼──────────────┐
          │ Open Library│  │ Comic Vine API     │
          │  Search API │  │ ComicBookRealm     │
          │  Works API  │  │ (HTML scraping)    │
          └─────────────┘  └────────────────────┘
```

**Request flow:**
1. Client sends `GET /api/v1/books?title=dune` with `X-API-Key` header
2. `deps.py` validates the API key via `require_api_key`
3. Route calls `BookService` which calls `BookRepository`
4. Repository queries PostgreSQL with filters + pagination
5. Response is serialized by Pydantic and returned as JSON

---

## 🌐 Data Sources

| Source | Type | Key Required | Status | Records |
|--------|------|-------------|--------|---------|
| [Open Library](https://openlibrary.org/developers/api) | Public API | No | ✅ Active | 233+ books |
| [Comic Vine](https://comicvine.gamespot.com/api/) | Public API | Yes (free) | ✅ Active | 1M+ issues |
| [ComicBookRealm](https://comicbookrealm.com) | HTML Scraping | No | ✅ Active | Browsable |
| [League of Comic Geeks](https://leagueofcomicgeeks.com) | HTML Scraping | Account | ⚠️ Blocked | See below |

### ⚠️ League of Comic Geeks — Cloudflare Protected

League of Comic Geeks is protected by **Cloudflare with JavaScript challenges**. All scraping attempts return HTTP 403 regardless of session cookies, because Cloudflare verifies that requests originate from a real browser by executing JavaScript — something `httpx` cannot do.

**Attempts made:**
- Direct scraping with `httpx` → HTTP 403
- Session cookies from authenticated account → HTTP 403 (Cloudflare challenge)

**Planned solution for v2:** Use [Playwright](https://playwright.dev/python/) (headless Chromium) which executes real JavaScript and can pass Cloudflare challenges:

```bash
pip install playwright
playwright install chromium
```

This is documented as a conscious technical decision — the scraper returns an empty list without breaking the weekly job.

---

## 📁 Project Structure

```
comics-books-api/
├── app/
│   ├── main.py                       Entry point — FastAPI app
│   ├── api/
│   │   ├── deps.py                   Centralized dependencies
│   │   └── routes/
│   │       ├── auth.py               GET /api/v1/auth/verify
│   │       ├── books.py              GET /api/v1/books, /books/{id}
│   │       └── comics.py             GET /api/v1/comics, /comics/{id}
│   ├── core/
│   │   ├── config.py                 Settings from .env
│   │   ├── security.py               X-API-Key validation
│   │   └── logging.py                Centralized logging setup
│   ├── db/
│   │   ├── database.py               Async engine + Base
│   │   └── session.py                AsyncSessionLocal
│   ├── models/
│   │   ├── book.py                   PostgreSQL books table
│   │   └── comic.py                  PostgreSQL comics table
│   ├── repositories/
│   │   ├── book_repository.py        All book DB queries
│   │   └── comic_repository.py       All comic DB queries
│   ├── services/
│   │   ├── book_service.py           Book business logic
│   │   ├── comic_service.py          Comic business logic
│   │   └── data_service.py           Scraper orchestrator
│   ├── scrapers/
│   │   ├── base_scraper.py           Abstract base class
│   │   ├── open_library.py           Open Library scraper ✅
│   │   ├── comic_vine.py             Comic Vine scraper ✅
│   │   ├── comicbookrealm.py         ComicBookRealm scraper ✅
│   │   └── league_of_comic_geeks.py  Blocked by Cloudflare ⚠️
│   ├── schemas/
│   │   ├── book_schema.py            Pydantic book schemas
│   │   └── comic_schema.py           Pydantic comic schemas
│   └── utils/
│       └── helpers.py                strip_html, safe_float, etc.
├── alembic/
│   └── env.py                        Async migrations
├── scripts/
│   └── run_scraper.py                Manual runner + weekly scheduler
├── tests/
│   ├── unit/
│   │   ├── test_scrapers.py          Parser unit tests (11 passing)
│   │   └── test_services.py          Service tests with mocked repos
│   └── integration/
│       └── test_api.py               Endpoint integration tests
├── .github/workflows/ci.yml          GitHub Actions CI
├── .env.example
├── alembic.ini
├── pyproject.toml
└── requirements.txt
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- PostgreSQL 14+ running locally

### Step 1 — Clone and set up environment

```bash
git clone https://github.com/yourusername/comics-books-api.git
cd comics-books-api

python -m venv venv
source venv/bin/activate        # Mac/Linux
# .\venv\Scripts\Activate.ps1   # Windows PowerShell

pip install -r requirements.txt
```

### Step 2 — Configure environment

```bash
cp .env.example .env
```

Edit `.env`:

```env
DATABASE_URL=postgresql+asyncpg://postgres:yourpassword@localhost:5432/comics_books_db
API_KEYS=generate-with-python-secrets
COMIC_VINE_API_KEY=your-key-from-comicvine.gamespot.com
DEBUG=false
```

Generate a secure API key:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### Step 3 — Create database and run migrations

```bash
# Create DB (run in psql)
CREATE DATABASE comics_books_db;

# Apply migrations
alembic upgrade head
```

### Step 4 — Start the API

```bash
uvicorn app.main:app --reload
```

Visit **http://localhost:8000/docs** for the interactive Swagger UI.

### Step 5 — Run the scraper (separate terminal)

```bash
.\venv\Scripts\Activate.ps1
python scripts/run_scraper.py
```

---

## ⚙️ Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL async connection string | — |
| `API_KEYS` | Comma-separated valid API keys | — |
| `COMIC_VINE_API_KEY` | Free key from comicvine.gamespot.com | — |
| `DEBUG` | Enable SQL query logging | `false` |
| `SCRAPER_DELAY_SECONDS` | Delay between HTTP requests | `1.5` |
| `SCRAPER_MAX_RETRIES` | Retry attempts per request | `3` |
| `SCRAPE_CRON` | APScheduler cron expression | `0 2 * * 1` |

---

## 📡 API Reference

All endpoints require `X-API-Key` header.

### Books

```http
GET /api/v1/books?title=dune&genre=fantasy&page=1&page_size=20
GET /api/v1/books/{id}
```

### Comics

```http
GET /api/v1/comics?publisher=Marvel&source=comic_vine&page=1
GET /api/v1/comics/{id}
```

### Auth

```http
GET /api/v1/auth/verify
```

**Example response — GET /api/v1/books:**

```json
{
  "total": 233,
  "page": 1,
  "page_size": 20,
  "results": [
    {
      "id": 1,
      "title": "Dune",
      "author": "Frank Herbert",
      "genres": ["science fiction"],
      "publish_year": 1965,
      "scraped_at": "2026-03-26T22:38:58"
    }
  ]
}
```

---

## 🕷 Running the Scraper

```bash
# Run all scrapers immediately + start weekly scheduler
python scripts/run_scraper.py
```

**First run results (March 26, 2026):**

| Scraper | Result |
|---------|--------|
| Open Library | ✅ 233 books |
| Comic Vine | ✅ Active (1M+ issues available) |
| ComicBookRealm | ✅ Active |
| League of Comic Geeks | ⚠️ 0 — Cloudflare blocked |

---

## 🧪 Running Tests

```bash
# All tests
pytest -v

# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v
```

Current status: **11 tests passing**

---

## ⚠️ Known Limitations

### League of Comic Geeks — Cloudflare
The site uses Cloudflare JavaScript challenges that block `httpx`-based scrapers. The scraper returns an empty list gracefully. Planned fix in v2 using Playwright headless browser.

### Comic Vine — User-Agent required
The Comic Vine API returns HTTP 403 without a browser-like `User-Agent` header, and HTTP 301 without `follow_redirects=True`. Both are handled in the scraper.

---

## 🚢 Deployment

### Railway (easiest)
1. Push repo to GitHub
2. Connect to railway.app
3. Add PostgreSQL service
4. Set environment variables
5. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6. Add second service for scraper: `python scripts/run_scraper.py`

### Render
Same as Railway — use Background Worker for the scraper service.

---

## 🛠 Tech Stack

| Tool | Purpose |
|------|---------|
| FastAPI 0.115 | Web framework + auto OpenAPI docs |
| SQLAlchemy 2.x | Async ORM |
| asyncpg | PostgreSQL async driver |
| Pydantic v2 | Data validation |
| httpx | Async HTTP client |
| BeautifulSoup4 | HTML parsing |
| APScheduler | Weekly cron scheduling |
| Alembic | DB migrations |
| pytest + respx | Testing |

---

## 📄 License

MIT License