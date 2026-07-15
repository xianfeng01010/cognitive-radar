import httpx
from app.config import settings


class SearXNGClient:
    def __init__(self):
        self.base_url = settings.SEARXNG_URL.rstrip("/")

    async def search(self, query: str, engines: str = "", limit: int = 20) -> list[dict]:
        params = {"q": query, "format": "json", "pageno": 1}
        if engines:
            params["engines"] = engines
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/search",
                params=params,
                timeout=15.0,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("results", [])[:limit]

    async def multi_search(self, query: str, engine_groups: list[str], limit_per_group: int = 10) -> dict[str, list[dict]]:
        import asyncio
        tasks = [
            self.search(query, engines=group, limit=limit_per_group)
            for group in engine_groups
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return {
            engine_groups[i]: r if not isinstance(r, Exception) else []
            for i, r in enumerate(results)
        }


searxng_client = SearXNGClient()