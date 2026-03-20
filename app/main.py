"""
Comics & Books API — main.py
Data sources: Open Library · Comic Vine · League of Comic Geeks
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import books, comics, auth
from app.core.config import settings
from app.core.logging import setup_logging
from app.db.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    await init_db()
    yield


app = FastAPI(
    title="Comics & Books API",
    description=(
        "REST API aggregating comic and book data from Open Library, "
        "Comic Vine, and League of Comic Geeks. "
        "Authenticate with X-API-Key header."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,   prefix="/api/v1", tags=["Auth"])
app.include_router(books.router,  prefix="/api/v1", tags=["Books"])
app.include_router(comics.router, prefix="/api/v1", tags=["Comics"])


@app.get("/", tags=["Health"])
async def root():
    return {"message": "Comics & Books API", "docs": "/docs", "version": "1.0.0"}


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok"}