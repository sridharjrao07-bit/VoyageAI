"""
Group Feature ORM Models

New tables:
  - allora_users              — simple user accounts for auth + group membership
  - trip_groups               — named planning groups
  - trip_group_members        — membership + per-group-member metadata
  - member_preferences        — preference vector per member per group
  - group_recommendation_runs — persisted scoring results (audit/replay)

All tables include created_at / updated_at; soft-delete via deleted_at.

Array-typed fields (tags) are stored as JSON text strings for max PostgreSQL
compat with asyncpg. Use json.loads() to consume them in Python.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, Column, DateTime, Enum, ForeignKey,
    Integer, String, Text, func,
)
from sqlalchemy.orm import relationship

from database import Base

# ── Helpers ────────────────────────────────────────────────────────────────────

def _now():
    return datetime.now(timezone.utc)


class TimestampMixin:
    created_at = Column(DateTime(timezone=True), default=_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=_now, onupdate=_now, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)  # soft-delete


# ── Users ──────────────────────────────────────────────────────────────────────

class AlloraUser(TimestampMixin, Base):
    """Platform user accounts (used for auth and group membership)."""
    __tablename__ = "allora_users"

    id = Column(String(36), primary_key=True)          # UUID string
    username = Column(String(64), unique=True, nullable=False, index=True)
    email = Column(String(256), unique=True, nullable=False, index=True)
    password_hash = Column(String(256), nullable=False)
    display_name = Column(String(128), nullable=False)
    avatar_emoji = Column(String(8), default="🧳")     # fun vanity field

    # Relationships
    owned_groups = relationship("TripGroup", back_populates="creator", foreign_keys="TripGroup.created_by")
    memberships = relationship("TripGroupMember", back_populates="user", foreign_keys="TripGroupMember.user_id")


# ── Trip Groups ────────────────────────────────────────────────────────────────

class TripGroup(TimestampMixin, Base):
    """A named trip planning group (e.g. 'Bali 2025')."""
    __tablename__ = "trip_groups"

    id = Column(String(36), primary_key=True)
    name = Column(String(256), nullable=False)
    created_by = Column(String(36), ForeignKey("allora_users.id"), nullable=False)
    status = Column(
        Enum("draft", "active", "completed", name="trip_group_status"),
        default="draft",
        nullable=False,
    )

    # Relationships
    creator = relationship("AlloraUser", back_populates="owned_groups", foreign_keys=[created_by])
    members = relationship("TripGroupMember", back_populates="group", cascade="all, delete-orphan")
    recommendation_runs = relationship("GroupRecommendationRun", back_populates="group", cascade="all, delete-orphan")


# ── Trip Group Members ─────────────────────────────────────────────────────────

class TripGroupMember(TimestampMixin, Base):
    """Maps a user to a trip group with a role and preference submission timestamp."""
    __tablename__ = "trip_group_members"

    id = Column(String(36), primary_key=True)
    group_id = Column(String(36), ForeignKey("trip_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("allora_users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(
        Enum("owner", "member", name="trip_group_role"),
        default="member",
        nullable=False,
    )
    joined_at = Column(DateTime(timezone=True), default=_now, nullable=False)
    preferences_submitted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    group = relationship("TripGroup", back_populates="members")
    user = relationship("AlloraUser", back_populates="memberships", foreign_keys=[user_id])
    preferences = relationship("MemberPreferences", back_populates="group_member", uselist=False, cascade="all, delete-orphan")


# ── Member Preferences ─────────────────────────────────────────────────────────

class MemberPreferences(TimestampMixin, Base):
    """Per-user, per-group preference vector submitted before a recommendation run."""
    __tablename__ = "member_preferences"

    id = Column(String(36), primary_key=True)
    group_member_id = Column(String(36), ForeignKey("trip_group_members.id", ondelete="CASCADE"), nullable=False, unique=True)

    # Stored as JSON text: '["beach", "budget", "food"]'
    preference_tags_json = Column(Text, default="[]")
    budget_min = Column(Integer, default=300)
    budget_max = Column(Integer, default=3000)
    trip_duration_days = Column(Integer, default=7)
    region_preference = Column(String(128), nullable=True)
    submitted_at = Column(DateTime(timezone=True), default=_now, nullable=False)

    # Relationships
    group_member = relationship("TripGroupMember", back_populates="preferences")

    # ── Convenience properties ──
    @property
    def preference_tags(self) -> list[str]:
        try:
            return json.loads(self.preference_tags_json or "[]")
        except (json.JSONDecodeError, TypeError):
            return []

    @preference_tags.setter
    def preference_tags(self, value: list[str]):
        self.preference_tags_json = json.dumps(value)

    def to_scoring_dict(self) -> dict:
        """Return a plain dict suitable for the scoring engine."""
        return {
            "id": self.group_member_id,
            "preference_tags": self.preference_tags,
            "budget_min": self.budget_min,
            "budget_max": self.budget_max,
            "trip_duration_days": self.trip_duration_days,
            "region_preference": self.region_preference,
        }


# ── Group Recommendation Runs ──────────────────────────────────────────────────

class GroupRecommendationRun(TimestampMixin, Base):
    """Persisted result of a fairness-aware scoring run (audit + replay support)."""
    __tablename__ = "group_recommendation_runs"

    id = Column(String(36), primary_key=True)
    group_id = Column(String(36), ForeignKey("trip_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    run_at = Column(DateTime(timezone=True), default=_now, nullable=False)
    algorithm_version = Column(String(32), default="1.0.0", nullable=False)
    result_payload_json = Column(Text, default="{}")  # full scored results JSON

    # Relationships
    group = relationship("TripGroup", back_populates="recommendation_runs")

    @property
    def result_payload(self) -> dict:
        try:
            return json.loads(self.result_payload_json or "{}")
        except (json.JSONDecodeError, TypeError):
            return {}

    @result_payload.setter
    def result_payload(self, value: dict):
        self.result_payload_json = json.dumps(value, default=str)
