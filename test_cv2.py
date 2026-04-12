import httpx
import os
from dotenv import load_dotenv
load_dotenv()

key = os.getenv("COMIC_VINE_API_KEY")
r = httpx.get(
    "https://comicvine.gamespot.com/api/issues/",
    params={"api_key": key, "format": "json", "limit": 1},
    headers={"User-Agent": "Mozilla/5.0"},
    follow_redirects=True,
)
print(f"Status: {r.status_code}")
print(f"Content-Type: {r.headers.get('content-type')}")
print(f"Body (500 chars): {r.text[:500]}")