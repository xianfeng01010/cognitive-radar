import httpx
from datetime import datetime
from typing import List, Optional, Dict, Any

from .base import RSSFeed, RSSEntry


class MinifluxAdapter:
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip("/")
        credentials = f"{username}:{password}"
        import base64
        encoded = base64.b64encode(credentials.encode()).decode()
        self.headers = {
            "Authorization": f"Basic {encoded}",
            "Content-Type": "application/json",
        }
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=self.headers,
                timeout=30.0,
            )
        return self._client

    async def add_feed(self, url: str, **kwargs) -> str:
        client = await self._get_client()
        response = await client.post("/v1/feeds", json={
            "feed_url": url,
            "category_id": kwargs.get("category_id", 1),
        })
        response.raise_for_status()
        return str(response.json()["feed_id"])

    async def remove_feed(self, feed_id: str) -> bool:
        client = await self._get_client()
        response = await client.delete(f"/v1/feeds/{feed_id}")
        return response.status_code == 204

    async def update_feed(self, feed_id: str, **kwargs) -> bool:
        payload = {}
        if "refresh_interval" in kwargs:
            payload["refresh_interval"] = kwargs["refresh_interval"]
        client = await self._get_client()
        response = await client.put(f"/v1/feeds/{feed_id}", json=payload)
        return response.status_code == 204

    async def get_feed(self, feed_id: str) -> Optional[RSSFeed]:
        client = await self._get_client()
        response = await client.get(f"/v1/feeds/{feed_id}")
        if response.status_code == 404:
            return None
        response.raise_for_status()
        d = response.json()
        return RSSFeed(
            id=str(d["id"]),
            url=d["feed_url"],
            title=d.get("title", ""),
            description=d.get("description"),
            last_updated=None,
            metadata={"site_url": d.get("site_url")},
        )

    async def list_feeds(self) -> List[RSSFeed]:
        client = await self._get_client()
        response = await client.get("/v1/feeds")
        response.raise_for_status()
        return [
            RSSFeed(
                id=str(f["id"]),
                url=f["feed_url"],
                title=f.get("title", ""),
                description=f.get("description"),
                last_updated=None,
                metadata={"site_url": f.get("site_url")},
            )
            for f in response.json()
        ]

    async def get_entries(self, feed_id: Optional[str] = None, since: Optional[datetime] = None, limit: int = 100) -> List[RSSEntry]:
        params = {"limit": limit, "status": "unread"}
        if feed_id:
            params["feed_id"] = feed_id
        if since:
            params["after"] = since.isoformat()

        client = await self._get_client()
        response = await client.get("/v1/entries", params=params)
        response.raise_for_status()
        entries_data = response.json().get("entries", [])

        return [
            RSSEntry(
                id=str(e["id"]),
                feed_id=str(e.get("feed", {}).get("id", "")),
                title=e.get("title", ""),
                content=e.get("content", ""),
                url=e.get("url", ""),
                author=e.get("author"),
                published_at=datetime.fromisoformat(e["published_at"]) if e.get("published_at") else None,
                collected_at=datetime.fromisoformat(e["created_at"]) if e.get("created_at") else datetime.utcnow(),
                content_hash=e.get("hash", ""),
                metadata={"status": e.get("status")},
            )
            for e in entries_data
        ]

    async def mark_read(self, entry_id: str) -> bool:
        client = await self._get_client()
        response = await client.put(f"/v1/entries/{entry_id}", json={"status": "read"})
        return response.status_code == 204

    async def health_check(self) -> Dict[str, Any]:
        try:
            client = await self._get_client()
            response = await client.get("/v1/me")
            if response.status_code == 200:
                return {"status": "healthy", "engine": "miniflux"}
            return {"status": "unhealthy", "error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}