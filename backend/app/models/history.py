import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.models.base import Base


class PushHistory(Base):
    __tablename__ = "push_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    buffer_item_id = Column(UUID(as_uuid=True), ForeignKey("buffer_items.id", ondelete="SET NULL"), nullable=True)
    push_tier = Column(String(20))  # important, normal, low
    content_snapshot = Column(JSONB, default=dict)
    trust_score_at_push = Column(Float, default=0.0)
    user_feedback = Column(String(20), nullable=True)  # like, dislike, None
    created_at = Column(DateTime, default=datetime.utcnow)


class SearchHistory(Base):
    __tablename__ = "search_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    keyword = Column(String(500), nullable=False)
    result_count = Column(Integer, default=0)
    report_id = Column(UUID(as_uuid=True), nullable=True)
    search_strength = Column(String(10), default="medium")  # strong, medium, weak
    created_at = Column(DateTime, default=datetime.utcnow)


class ViewHistory(Base):
    __tablename__ = "view_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content_type = Column(String(20))  # entry, case, push
    content_id = Column(UUID(as_uuid=True), nullable=True)
    content_title = Column(Text, nullable=True)
    source = Column(String(20))  # push, search, browse
    url = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class HealthReport(Base):
    __tablename__ = "health_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_data = Column(JSONB, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class DeleteLog(Base):
    __tablename__ = "delete_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    delete_type = Column(String(50))
    deleted_ids = Column(JSONB, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)