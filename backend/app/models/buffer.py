import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.models.base import Base


class BufferItem(Base):
    __tablename__ = "buffer_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entry_id = Column(UUID(as_uuid=True), ForeignKey("entries.id", ondelete="CASCADE"))
    status = Column(String(20), default="pending")  # pending, verified, pushed, rejected
    priority_score = Column(Float, default=0.0)
    verification_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    metadata_ = Column("metadata", JSONB, default=dict)

    verifications = relationship("Verification", back_populates="buffer_item", cascade="all, delete-orphan")


class Verification(Base):
    __tablename__ = "verifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    buffer_item_id = Column(UUID(as_uuid=True), ForeignKey("buffer_items.id", ondelete="CASCADE"))
    search_keywords = Column(JSONB, default=list)
    search_engine = Column(String(50), nullable=True)
    results = Column(JSONB, default=list)
    status = Column(String(20), default="pending")  # pending, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    buffer_item = relationship("BufferItem", back_populates="verifications")