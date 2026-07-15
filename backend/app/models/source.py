import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text, JSON, CHAR
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.models.base import Base


class Source(Base):
    __tablename__ = "sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    url = Column(Text, nullable=False, unique=True)
    source_type = Column(CHAR(1), nullable=False)
    cache_level = Column(CHAR(2), nullable=False, default="L2")
    trust_score = Column(Float, default=50.0)
    status = Column(String(20), default="active")
    miniflux_feed_id = Column(String(50), nullable=True)
    refresh_interval_sec = Column(Integer, default=3600)
    hit_count = Column(Integer, default=0)
    weighted_hit_score = Column(Float, default=0.0)
    last_hit_at = Column(DateTime, nullable=True)
    added_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    added_by_search = Column(String(255), nullable=True)
    metadata_ = Column("metadata", JSONB, default={})


class Entry(Base):
    __tablename__ = "entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(UUID(as_uuid=True), ForeignKey("sources.id"))
    title = Column(Text)
    content = Column(Text)
    url = Column(Text, unique=True)
    author = Column(String(255), nullable=True)
    published_at = Column(DateTime, nullable=True)
    collected_at = Column(DateTime, default=datetime.utcnow)
    content_type = Column(String(50), nullable=True)
    language = Column(CHAR(2), default="zh")
    content_hash = Column(String(64), nullable=True)
    keywords = Column(JSONB, default=[])
    metadata_ = Column("metadata", JSONB, default={})