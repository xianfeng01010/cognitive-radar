from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, List, Optional, Dict, Any


@dataclass
class RSSFeed:
    id: str
    url: str
    title: str
    description: Optional[str]
    last_updated: Optional[datetime]
    metadata: Dict[str, Any]


@dataclass
class RSSEntry:
    id: str
    feed_id: str
    title: str
    content: str
    url: str
    author: Optional[str]
    published_at: Optional[datetime]
    collected_at: datetime
    content_hash: str
    metadata: Dict[str, Any]


class RSSEngine(Protocol):
    async def add_feed(self, url: str, **kwargs) -> str: ...
    async def remove_feed(self, feed_id: str) -> bool: ...
    async def update_feed(self, feed_id: str, **kwargs) -> bool: ...
    async def get_feed(self, feed_id: str) -> Optional[RSSFeed]: ...
    async def list_feeds(self) -> List[RSSFeed]: ...
    async def get_entries(self, feed_id: Optional[str] = None, since: Optional[datetime] = None, limit: int = 100) -> List[RSSEntry]: ...
    async def mark_read(self, entry_id: str) -> bool: ...
    async def health_check(self) -> Dict[str, Any]: ...