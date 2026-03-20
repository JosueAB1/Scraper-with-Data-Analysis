"""
app/utils/helpers.py
=====================
Shared utility functions used across scrapers and services.
"""

import re


def strip_html(text: str) -> str:
    """Remove HTML tags from a string."""
    return re.sub(r"<[^>]+>", "", text).strip()


def truncate_list(items: list, max_items: int = 10, separator: str = ", ") -> str:
    """Join a list into a comma-separated string, capped at max_items."""
    return separator.join(str(i) for i in items[:max_items])


def safe_float(value) -> float | None:
    """Convert a value to float, returning None on failure."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def safe_int(value) -> int | None:
    """Convert a value to int, returning None on failure."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return None