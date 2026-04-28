"""
SQLAlchemy ORM Models for Allora (PostgreSQL + pgvector)

Tables:
  - destinations       — master destination catalogue with vector embeddings
  - rec_history        — per-user recommendation history
  - user_likes         — bucket-list / liked destinations (RL feedback loop)
  - user_comments      — community reviews for Social Intelligence Agent
"""
from __future__ import annotations

from datetime import datetime
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    func,
)
from pgvector.sqlalchemy import Vector

from database import Base


class Destination(Base):
    __tablename__ = "destinations"

    id = Column(String, primary_key=True)
    name = Column(String(256), nullable=False, index=True)
    country = Column(String(128))
    continent = Column(String(64))
    description = Column(Text, default="")
    tags = Column(Text, default="")
    climate = Column(String(64))
    best_season = Column(String(64))
    avg_cost_usd = Column(Float, default=0.0)
    latitude = Column(Float)
    longitude = Column(Float)
    accessibility = Column(String(16), default="false")
    popularity = Column(Float, default=0.0)

    # pgvector column — 384 dims for all-MiniLM-L6-v2 (text search)
    embedding = Column(Vector(384))

    # pgvector column — 512 dims for CLIP (visual search)
    clip_embedding = Column(Vector(512))

    # ── Group Feature Columns (added non-breaking) ──────────────────────────
    # Stored as JSON text arrays, e.g. '["beach","budget","food"]'
    activity_tags = Column(Text, nullable=True)
    budget_tier_min = Column(Integer, nullable=True)
    budget_tier_max = Column(Integer, nullable=True)
    parallel_value_tags = Column(Text, nullable=True)

    # Soft-delete support
    deleted_at = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<Destination {self.id} {self.name}>"


class RecHistory(Base):
    __tablename__ = "rec_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False, index=True)
    destination_id = Column(String, nullable=False)
    timestamp = Column(DateTime, default=func.now())
    deleted_at = Column(DateTime, nullable=True)


class UserLike(Base):
    __tablename__ = "user_likes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False, index=True)
    destination_id = Column(String, nullable=False)
    categories = Column(Text, nullable=False, default="")
    timestamp = Column(DateTime, default=func.now())


class UserComment(Base):
    __tablename__ = "user_comments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    destination_id = Column(String, nullable=False, index=True)
    user_id = Column(String, nullable=False)
    comment_text = Column(Text, nullable=False)
    rating = Column(Integer, default=5)
    timestamp = Column(DateTime, default=func.now())
    is_verified_visit = Column(Boolean, default=False)
