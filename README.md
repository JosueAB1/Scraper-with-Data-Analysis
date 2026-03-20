# Scraper-with-Data-Analysis
A Python scraper to extracts data, stores it and generates visual insights with Pandas

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
- [Deployment](#-deployment)

---

## ✨ Features

- **REST API** with full OpenAPI / Swagger documentation (`/docs`)
- **API Key authentication** via `X-API-Key` header
- **Search** by title and author (case-insensitive partial match)
- **Filter** by genre, publisher, and data source
- **Pagination** on all list endpoints
- **Async scrapers** for 3 data sources (see below)
- **Weekly scheduled scraping** via APScheduler (cron)
- **PostgreSQL** storage with SQLAlchemy 2.x async ORM
- **Upsert logic** — re-running the scraper is always safe
- **pytest test suite** with mocked HTTP calls (no real network in CI)
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
              └──────┬──────────────┬────────┘
                     │              │
          ┌──────────▼──┐    ┌──────▼──────────────────┐
          │ Open Library│    │ Comic Vine API (official) │
          │  Search API │    │ League of Comic Geeks     │
          │  Works API  │    │ (HTML scraping)           │
          └─────────────┘    └───────────────────────────┘
```

**Request flow:**
1. Client sends `GET /api/v1/books?title=dune` with `X-API-Key: <key>` header
2. FastAPI validates the API key via the `require_api_key` dependency
3. Route handler queries PostgreSQL with filters + pagination
4. Response is serialized by Pydantic and returned as JSON

**Scraper flow (weekly):**
1. APScheduler triggers `run_all_scrapers()` every Monday at 02:00 UTC
2. Each scraper fetches data with polite delays between requests
3. Data is upserted into PostgreSQL (safe to run multiple times)

---

## 🌐 Data Sources

| Source | Type | Data |
|--------|------|------|
| [Open Library](https://openlibrary.org/developers/api) | Public API (no key needed) | Books: title, author, genres, description, cover, ISBN |
| [Comic Vine](https://comicvine.gamespot.com/api/) | Public API (free key) | Comics: issues, publisher, characters, cover, dates |
| [League of Comic Geeks](https://leagueofcomicgeeks.com) | HTML scraping | Comics: new releases, ratings, publisher |

---

## 📁 Project Structure

```
comics-books-api/
├── app/
│   ├── main.py                  # FastAPI app, middleware, router registration
│   ├── api/
│   │   └── routes/
│   │       ├── auth.py          # GET /auth/verify
│   │       ├── books.py         # GET /books, GET /books/{id}
│   │       └── comics.py        # GET /comics, GET /comics/{id}
│   ├── core/
│   │   ├── config.py            # Settings loaded from .env (pydantic-settings)
│   │   └── security.py          # API Key dependency
│   ├── db/
│   │   └── database.py          # Async engine, session factory, Base, init_db
│   ├── models/
│   │   ├── book.py              # SQLAlchemy Book ORM model
│   │   └── comic.py             # SQLAlchemy Comic ORM model
│   ├── schemas/
│   │   └── schemas.py           # Pydantic request/response schemas
│   ├── scrapers/
│   │   ├── open_library.py      # Open Library scraper
│   │   ├── comic_vine.py        # Comic Vine API scraper
│   │   └── league_of_comic_geeks.py  # HTML scraper
│   └── services/
│       └── data_service.py      # Upsert logic (scraper → DB bridge)
├── scripts/
│   └── run_scraper.py           # Standalone scraper runner + scheduler
├── tests/
│   ├── test_scrapers/
│   │   └── test_scrapers.py     # Unit tests for parser functions
│   └── test_routes/
│       └── test_api.py          # Integration tests for API endpoints
├── .github/
│   └── workflows/
│       └── ci.yml               # GitHub Actions CI pipeline
├── .env.example                 # Template for environment variables
├── .gitignore
├── pytest.ini
├── requirements.txt
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- PostgreSQL 14+ running locally (or a hosted instance)

### Step 1 — Clone the repository

```bash
git clone https://github.com/yourusername/comics-books-api.git
cd comics-books-api
```

### Step 2 — Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows
```

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4 — Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in your values:

```env
DATABASE_URL=postgresql+asyncpg://postgres:yourpassword@localhost:5432/comics_books_db
API_KEYS=my-secret-key-123
COMIC_VINE_API_KEY=your_comic_vine_key   # get free at comicvine.gamespot.com/api/
```

### Step 5 — Create the database

```bash
# In psql or pgAdmin, run:
CREATE DATABASE comics_books_db;
```

Tables are created automatically when the app starts.

### Step 6 — Start the API server

```bash
uvicorn app.main:app --reload
```

Visit **http://localhost:8000/docs** to explore the interactive Swagger UI.

---

## ⚙️ Configuration

All configuration is done via environment variables (loaded from `.env`):

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL async connection string | `postgresql+asyncpg://...` |
| `API_KEYS` | Comma-separated valid API keys | `change-me-in-env` |
| `COMIC_VINE_API_KEY` | Your Comic Vine API key | _(empty)_ |
| `ALLOWED_ORIGINS` | CORS origins (JSON array) | `["*"]` |
| `SCRAPER_DELAY_SECONDS` | Polite delay between scraper requests | `1.5` |
| `SCRAPER_MAX_RETRIES` | Retry attempts per failed request | `3` |
| `SCRAPE_CRON` | APScheduler cron expression | `0 2 * * 1` (Monday 2am) |

---

## 📡 API Reference

All endpoints require the `X-API-Key` header.

### Authentication

```http
GET /api/v1/auth/verify
X-API-Key: your-api-key
```

```json
{ "status": "authenticated", "key_prefix": "your-api..." }
```

---

### Books

#### List books

```http
GET /api/v1/books
X-API-Key: your-api-key
```

**Query parameters:**

| Param | Type | Description |
|-------|------|-------------|
| `title` | string | Partial title search |
| `author` | string | Partial author search |
| `genre` | string | Filter by genre |
| `page` | int | Page number (default: 1) |
| `page_size` | int | Results per page (1–100, default: 20) |

**Example request:**

```bash
curl -H "X-API-Key: your-api-key" \
  "http://localhost:8000/api/v1/books?genre=fantasy&page=1&page_size=5"
```

**Example response:**

```json
{
  "total": 142,
  "page": 1,
  "page_size": 5,
  "results": [
    {
      "id": 1,
      "title": "A Wizard of Earthsea",
      "author": "Ursula K. Le Guin",
      "genres": ["fantasy", "young adult"],
      "publish_year": 1968,
      "page_count": 183,
      "cover_url": "https://covers.openlibrary.org/b/id/8739161-M.jpg",
      "scraped_at": "2024-11-18T02:00:00"
    }
  ]
}
```

#### Get book by ID

```bash
curl -H "X-API-Key: your-api-key" \
  "http://localhost:8000/api/v1/books/1"
```

---

### Comics

#### List comics

```http
GET /api/v1/comics
X-API-Key: your-api-key
```

**Query parameters:**

| Param | Type | Description |
|-------|------|-------------|
| `title` | string | Partial title search |
| `genre` | string | Filter by genre |
| `publisher` | string | Filter by publisher (e.g. `Marvel`) |
| `source` | string | `comic_vine` or `league_of_comic_geeks` |
| `page` | int | Page number |
| `page_size` | int | Results per page (1–100) |

**Example request:**

```bash
curl -H "X-API-Key: your-api-key" \
  "http://localhost:8000/api/v1/comics?publisher=Marvel&page=1"
```

**Example response:**

```json
{
  "total": 87,
  "page": 1,
  "page_size": 20,
  "results": [
    {
      "id": 3,
      "title": "Amazing Spider-Man",
      "issue_number": "1",
      "publisher": "Marvel",
      "characters": ["Spider-Man", "Mary Jane"],
      "cover_url": "https://comicvine.gamespot.com/...",
      "publish_date": "2022-01-01",
      "source": "comic_vine",
      "scraped_at": "2024-11-18T02:00:00"
    }
  ]
}
```

#### Get comic by ID

```bash
curl -H "X-API-Key: your-api-key" \
  "http://localhost:8000/api/v1/comics/3"
```

---

## 🕷 Running the Scraper

### Manual run (one-time)

```bash
python scripts/run_scraper.py
```

This runs all three scrapers immediately, then starts the weekly scheduler.

### Scheduler only (skip immediate run)

To run only the scheduler without the immediate first run, edit `scripts/run_scraper.py` and comment out the `await run_all_scrapers()` line before the scheduler start.

---

## 🧪 Running Tests

```bash
pytest -v
```

Tests are fully isolated — they mock all HTTP calls and database sessions. No real network or database required.

```
tests/test_scrapers/test_scrapers.py  ← Parser unit tests
tests/test_routes/test_api.py         ← API integration tests
```

---

## 🚢 Deployment

### Option A — Run on a VPS (e.g. DigitalOcean, Hetzner)

```bash
# On your server:
git clone https://github.com/yourusername/comics-books-api.git
cd comics-books-api
pip install -r requirements.txt
cp .env.example .env && nano .env

# Start API (use a process manager like systemd or supervisor in production)
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Start scraper scheduler in a separate process
python scripts/run_scraper.py
```

### Option B — Railway / Render (free tier)

1. Push this repo to GitHub
2. Connect to Railway or Render
3. Add environment variables in the dashboard
4. Set start command to `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

---

## 🛠 Tech Stack

| Tool | Purpose |
|------|---------|
| [FastAPI](https://fastapi.tiangolo.com) | Web framework + OpenAPI docs |
| [SQLAlchemy 2.x](https://docs.sqlalchemy.org) | Async ORM |
| [asyncpg](https://github.com/MagicStack/asyncpg) | PostgreSQL async driver |
| [Pydantic v2](https://docs.pydantic.dev) | Data validation & serialization |
| [httpx](https://www.python-httpx.org) | Async HTTP client for scrapers |
| [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/) | HTML parsing |
| [APScheduler](https://apscheduler.readthedocs.io) | Weekly cron scheduling |
| [pytest](https://pytest.org) + [respx](https://lundberg.github.io/respx/) | Testing |

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.