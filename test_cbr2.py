import httpx

url = "https://comicbookrealm.com/search/comics/?a=search&series=search&method=all&q=Marvel&page=1"
r = httpx.get(
    url,
    headers={"User-Agent": "Mozilla/5.0"},
    follow_redirects=True,
)
print(f"Status: {r.status_code}")
print(f"Final URL: {r.url}")
print(f"HTML (2000 chars):\n{r.text[:2000]}")