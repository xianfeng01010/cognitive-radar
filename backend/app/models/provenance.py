import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.models.base import Base


class ProvenanceTree(Base):
    __tablename__ = "provenance_trees"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content_id = Column(UUID(as_uuid=True), nullable=True)
    conclusion = Column(Text)
    tree_data = Column(JSONB, nullable=False)
    hash = Column(String(64), nullable=False)
    prev_hash = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Case(Base):
    __tablename__ = "cases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(Text)
    who = Column(JSONB, default=dict)
    timeline_data = Column("timeline", JSONB, default=list)
    key_decisions = Column(JSONB, default=list)
    outcome = Column(Text)
    source_url = Column(Text)
    source_id = Column(UUID(as_uuid=True), ForeignKey("sources.id", ondelete="SET NULL"), nullable=True)
    trust_score = Column(Float, default=50.0)
    verification_status = Column(String(20), default="pending")  # pending, verified, rejected
    related_keywords = Column(JSONB, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)

    source = relationship("Source")