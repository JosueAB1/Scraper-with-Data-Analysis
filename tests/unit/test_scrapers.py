"""
tests/unit/test_scrapers.py
============================
Unit tests for parser functions (no network, no DB).
"""

import pytest
from app.scrapers.open_library import OpenLibraryScraper
from app.scrapers.comic_vine import ComicVineScraper
from app.utils.helpers import strip_html, safe_float, safe_int


# ── Helpers ───────────────────────────────────────────────────────────────────

def test_strip_html():
    assert strip_html("<p>Hello <b>world</b></p>") == "Hello world"
    assert strip_html("No tags here") == "No tags here"
    assert strip_html("") == ""


def test_safe_float():
    assert safe_float("3.5") == 3.5
    assert safe_float("not a number") is None
    assert safe_float(None) is None


def test_safe_int():
    assert safe_int("42") == 42
    assert safe_int("abc") is None
    assert safe_int(None) is None


# ── Open Library parser ───────────────────────────────────────────────────────

def test_parse_book_full():
    doc = {
        "key": "/works/OL12345W",
        "title": "Dune",
        "author_name": ["Frank Herbert"],
        "cover_i": 9999,
        "subject": ["science fiction", "desert planets"],
        "first_publish_year": 1965,
        "number_of_pages_median": 412,
        "publisher": ["Chilton Books"],
        "isbn": ["9780441013593"],
        "language": ["eng"],
    }
    result = OpenLibraryScraper._parse_book(doc, "A desert planet epic.")
    assert result["title"] == "Dune"
    assert result["author"] == "Frank Herbert"
    assert result["publish_year"] == 1965
    assert result["open_library_id"] == "OL12345W"
    assert "science fiction" in result["genres"]
    assert result["description"] == "A desert planet epic."


def test_parse_book_minimal():
    doc = {"key": "/works/OL99W", "title": "Minimal Book"}
    result = OpenLibraryScraper._parse_book(doc, "")
    assert result["title"] == "Minimal Book"
    assert result["author"] == ""
    assert result["cover_url"] is None
    assert result["description"] is None


# ── Comic Vine parser ─────────────────────────────────────────────────────────

def test_parse_issue_full():
    issue = {
        "id": 42,
        "name": "The Amazing Issue",
        "issue_number": "1",
        "volume": {"name": "Amazing Comics"},
        "cover_date": "2024-01-01",
        "image": {"medium_url": "https://example.com/cover.jpg"},
        "description": "<p>A great story.</p>",
        "deck": "Short summary.",
        "character_credits": [{"name": "Spider-Man"}, {"name": "Iron Man"}],
        "site_detail_url": "https://comicvine.gamespot.com/issue/42",
    }
    result = ComicVineScraper._parse_issue(issue)
    assert result["comic_vine_id"] == "42"
    assert result["title"] == "The Amazing Issue"
    assert result["publish_date"] == "2024-01-01"
    assert "Spider-Man" in result["characters"]
    assert result["source"] == "comic_vine"
    assert "<p>" not in result["description"]


def test_parse_issue_minimal():
    issue = {"id": 1, "volume": {}}
    result = ComicVineScraper._parse_issue(issue)
    assert result["comic_vine_id"] == "1"
    assert result["title"] == "Unknown"