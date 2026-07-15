from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import Optional, Any


class SourceCreate(BaseModel):
    url: str
    name: str = ""
    source_type: str = "R"
    cache_level: str = "L2"
    refresh_interval_sec: int = 3600


class SourceUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    refresh_interval_sec: Optional[int] = None
    cache_level: Optional[str] = None


class SourceOut(BaseModel):
    id: UUID
    name: str
    url: str
    source_type: str
    cache_level: str
    trust_score: float
    status: str
    miniflux_feed_id: Optional[str] = None
    hit_count: int
    last_hit_at: Optional[datetime] = None
    added_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ScanRequest(BaseModel):
    keyword: str = Field(..., min_length=1, max_length=500)
    skip_searxng: bool = False


class CardItem(BaseModel):
    id: str = ""
    title: str = ""
    content_preview: str = ""
    source: str = ""
    url: str = ""
    cache_level: str = ""  # L1, L2, SearXNG
    trust_score: float = 0.0
    published_date: str = ""


class ScanResult(BaseModel):
    keyword: str
    strength: str
    cards: list[CardItem] = []
    total: int = 0
    clustered: Optional[dict] = None
    report: Optional[dict] = None


class CardDetailRequest(BaseModel):
    title: str
    content: str = ""
    url: str = ""
    source: str = ""


class CardDetailResponse(BaseModel):
    title: str
    tldr: str = ""
    key_findings: list[str] = []
    key_entities: list[str] = []
    timeline: list[str] = []
    conclusion: str = ""
    source_url: str = ""


class PushOut(BaseModel):
    id: UUID
    push_tier: str
    content_snapshot: dict
    trust_score_at_push: float
    user_feedback: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class PushFeedback(BaseModel):
    feedback: str  # "like" or "dislike"


class SearchHistoryOut(BaseModel):
    id: UUID
    keyword: str
    result_count: int
    search_strength: str
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ViewHistoryOut(BaseModel):
    id: UUID
    content_type: Optional[str] = None
    content_title: Optional[str] = None
    source: Optional[str] = None
    url: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class HealthOut(BaseModel):
    status: str
    components: dict[str, Any]