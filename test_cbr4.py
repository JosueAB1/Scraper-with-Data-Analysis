"""
Test: verify ComicBookRealm series list page structure
Run: python test_cbr4.py
"""
import httpx
from bs4 import BeautifulSoup

url = "https://comicbookrealm.com/report/series/list/a"
r = httpx.get(
    url,
    headers={"User-Agent": "Mozilla/5.0"},
    follow_redirects=True,
)
print(f"Status: {r.status_code}")
print(f"Final URL: {r.url}")

soup = BeautifulSoup(r.text, "html.parser")
title = soup.find("title")
print(f"Page title: {title.text if title else 'N/A'}")
print()

# Show all tags with classes that could be comic listings
print("=== Tags with relevant classes ===")
for tag in soup.find_all(class_=True):
    classes = " ".join(tag.get("class", []))
    if any(k in classes.lower() for k in ["series", "comic", "list", "row", "item", "result"]):
        text = tag.get_text(strip=True)[:80]
        print(f"  {tag.name}.{classes}: {text}")

print()
print("=== All links containing /series/ or /comic/ ===")
links = soup.select("a[href*='/series/'], a[href*='/comic/']")
print(f"Found {len(links)} links")
for link in links[:10]:
    print(f"  {link.get('href')} → {link.get_text(strip=True)[:60]}")