import httpx, os, json
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
print(f"Encoding detectado: {r.encoding}")
print(f"Content length: {len(r.content)} bytes")

# Intentar parsear directamente
try:
    data = r.json()
    print(f"JSON OK — status_detail: {data.get('status_detail')}")
except Exception as e:
    print(f"r.json() fallo: {e}")

# Intentar con content
try:
    data = json.loads(r.content.decode("utf-8"))
    print(f"content.decode OK")
except Exception as e:
    print(f"content.decode fallo: {e}")
    print(f"Primeros bytes: {r.content[:20]}")