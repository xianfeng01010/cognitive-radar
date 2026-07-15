import httpx
from app.config import settings

MEILI_URL = settings.MEILI_URL.rstrip("/")
MEILI_KEY = settings.MEILI_KEY
_headers = {"Authorization": f"Bearer {MEILI_KEY}"}

INDEX_ENTRIES = "entries"
INDEX_CASES = "cases"
INDEX_PROVENANCE = "provenance_trees"

_client: httpx.AsyncClient | None = None


async def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(base_url=MEILI_URL, headers=_headers, timeout=10.0)
    return _client


async def init_indexes():
    client = await _get_client()
    for index_uid in [INDEX_ENTRIES, INDEX_CASES, INDEX_PROVENANCE]:
        try:
            await client.get(f"/indexes/{index_uid}")
        except httpx.HTTPStatusError:
            await client.post("/indexes", json={"uid": index_uid, "primaryKey": "id"})

    await client.put(f"/indexes/{INDEX_ENTRIES}/settings", json={
        "searchableAttributes": ["title", "content", "keywords"],
        "filterableAttributes": ["source_type", "source_id", "published_at"],
        "sortableAttributes": ["published_at", "collected_at"],
    })
    await client.put(f"/indexes/{INDEX_CASES}/settings", json={
        "searchableAttributes": ["title", "who", "outcome", "related_keywords"],
        "filterableAttributes": ["verification_status", "trust_score"],
    })


async def add_documents(index_uid: str, documents: list[dict]):
    client = await _get_client()
    resp = await client.post(f"/indexes/{index_uid}/documents?primaryKey=id", json=documents)
    resp.raise_for_status()
    return resp.json()


async def search_entries(query: str, limit: int = 20, filters: str = "") -> list[dict]:
    client = await _get_client()
    opts = {"limit": limit}
    if filters:
        opts["filter"] = filters
    resp = await client.post(f"/indexes/{INDEX_ENTRIES}/search", json={"q": query, **opts})
    resp.raise_for_status()
    return resp.json().get("hits", [])


async def search_cases(query: str, limit: int = 10) -> list[dict]:
    client = await _get_client()
    resp = await client.post(f"/indexes/{INDEX_CASES}/search", json={"q": query, "limit": limit})
    resp.raise_for_status()
    return resp.json().get("hits", [])


async def health() -> dict:
    client = await _get_client()
    try:
        resp = await client.get("/health")
        resp.raise_for_status()
        return {"status": "healthy"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}