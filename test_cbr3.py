import httpx
from bs4 import BeautifulSoup

url = "https://comicbookrealm.com/search/comics/?a=search&series=search&method=all&q=Marvel&page=1"
r = httpx.get(
    url,
    headers={"User-Agent": "Mozilla/5.0"},
    follow_redirects=True,
)
soup = BeautifulSoup(r.text, "html.parser")

# Ver todos los tags con clases que contengan "result", "comic", "series", "item"
for tag in soup.find_all(class_=True):
    classes = " ".join(tag.get("class", []))
    if any(k in classes.lower() for k in ["result", "comic", "series", "item", "list", "row"]):
        print(f"TAG: {tag.name} | CLASS: {classes}")
        print(f"  TEXT: {tag.get_text(strip=True)[:80]}")
        print()