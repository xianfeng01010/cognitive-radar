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


class ScanResult(BaseModel):
    keyword: str
    strength: str
    l1_results: list[dict] = []
    l2_results: list[dict] = []
    searxng_results: list[dict] = []
    total: int = 0
    clustered: Optional[dict] = None
    report: Optional[dict] = None


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