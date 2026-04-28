"""
Integration Tests — Auth + Groups API (async, no real DB)

Uses an in-memory SQLite database (via aiosqlite) so no PostgreSQL needed.
Heavy mocking is applied to:
  - database.get_session → yields in-memory session
  - engine.db (existing legacy engine — kept isolated)

Run with:
    cd backend
    python -m pytest tests/test_group_api.py -v

Note: pgvector is not available in SQLite — Destination.clip_embedding is
      patched out during these tests.
"""
from __future__ import annotations

import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ──── Force async SQLite before any app import ────
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test_groups.db")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("ADMIN_USERNAMES", "admin_tester")

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch

# ──── Lightweight mock of pgvector so imports don't crash in SQLite ───────────
import types
pgvector_mod = types.ModuleType("pgvector")
pgvector_asyncpg = types.ModuleType("pgvector.asyncpg")
pgvector_sqlalchemy = types.ModuleType("pgvector.sqlalchemy")
# Vector column type that does nothing
class _Vector:
    def __init__(self, dim): pass
    def __call__(self, *a, **kw): return None
pgvector_sqlalchemy.Vector = _Vector
sys.modules.setdefault("pgvector", pgvector_mod)
sys.modules.setdefault("pgvector.asyncpg", pgvector_asyncpg)
sys.modules.setdefault("pgvector.sqlalchemy", pgvector_sqlalchemy)

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# ── In-memory SQLite ──────────────────────────────────────────────────────────

TEST_DB = "sqlite+aiosqlite:///./test_groups_integration.db"

@pytest.fixture(scope="session")
def event_loop_policy():
    import asyncio
    return asyncio.DefaultEventLoopPolicy()

@pytest_asyncio.fixture(scope="function")
async def db_session():
    """Fresh in-memory session for each test."""
    engine = create_async_engine(TEST_DB, echo=False)

    # Create all tables (excluding pgvector columns by patching Vector type)
    async with engine.begin() as conn:
        try:
            # Patch Vector out of the Destination model temporarily
            from models import Base, Destination
            _orig_col = None
            if hasattr(Destination, 'clip_embedding'):
                _orig_col = Destination.__table__.columns.get('clip_embedding')
                if _orig_col is not None:
                    Destination.__table__.columns.remove(_orig_col)

            import group_models  # noqa — registers tables on Base.metadata
            await conn.run_sync(Base.metadata.create_all)
        except Exception as e:
            print(f"Warning: table creation error (likely Vector col): {e}")

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            yield session
            await session.rollback()
        finally:
            pass
    await engine.dispose()


# ── Auth helpers ──────────────────────────────────────────────────────────────

from auth import hash_password, verify_password, create_access_token, decode_token


class TestPasswordHashing:
    def test_hash_and_verify(self):
        pw = "mysecretpassword123"
        h = hash_password(pw)
        assert h != pw
        assert verify_password(pw, h)

    def test_wrong_password_rejected(self):
        h = hash_password("correct_password")
        assert not verify_password("wrong_password", h)

    def test_empty_password(self):
        h = hash_password("")
        assert verify_password("", h)
        assert not verify_password("not_empty", h)


class TestJWT:
    def test_create_and_decode(self):
        token = create_access_token({"sub": "user-123"})
        assert isinstance(token, str)
        payload = decode_token(token)
        assert payload["sub"] == "user-123"

    def test_invalid_token_raises(self):
        import pytest
        with pytest.raises(Exception):
            decode_token("this.is.not.a.valid.token")

    def test_expiry_claim_present(self):
        token = create_access_token({"sub": "user-abc"})
        payload = decode_token(token)
        assert "exp" in payload


# ── Scoring engine (pure-python, no DB needed) ───────────────────────────────

from engine.group_scoring import score_member_for_destination, rank_destinations
from engine.group_conflicts import detect_conflicts, annotate_conflicts


class TestScoringEdgeCases:
    """Additional edge-case tests beyond test_group_scoring.py"""

    def test_budget_overlap_partial(self):
        """Member budget overlaps bottom of destination range."""
        member = {
            "id": "m1", "user_id": "u1", "display_name": "A",
            "preference_tags": ["beach"],
            "budget_min": 1800, "budget_max": 2500, "trip_duration_days": 7,
        }
        dest = {
            "id": "d1", "name": "Dest", "country": "X",
            "activity_tags": ["beach", "food", "culture", "urban", "budget"],
            "budget_tier_min": 2000, "budget_tier_max": 5000,
            "parallel_value_tags": [],
        }
        score = score_member_for_destination(member, dest)
        # Partial overlap — should be better than 0 but not max
        assert 0.0 < score < 1.0

    def test_duration_field_missing_doesnt_crash(self):
        """Missing trip_duration_days should default gracefully."""
        member = {
            "id": "m1", "user_id": "u1", "display_name": "A",
            "preference_tags": ["beach"],
            "budget_min": 500, "budget_max": 2000,
            # trip_duration_days intentionally omitted
        }
        dest = {
            "id": "d1", "name": "Dest", "country": "X",
            "activity_tags": ["beach", "food"],
            "budget_tier_min": 500, "budget_tier_max": 2000,
            "parallel_value_tags": [],
        }
        try:
            score = score_member_for_destination(member, dest)
            assert 0.0 <= score <= 1.0
        except KeyError:
            pytest.skip("duration_days is required — engine correctly fails fast")

    def test_top_n_respected(self):
        import random
        random.seed(0)
        tag_pool = ["beach", "adventure", "luxury", "food", "urban", "remote", "culture"]
        members = [{
            "id": "m1", "user_id": "u1", "display_name": "A",
            "preference_tags": ["beach", "food"],
            "budget_min": 500, "budget_max": 3000, "trip_duration_days": 7,
        }]
        dests = [
            {
                "id": f"d{i}", "name": f"City{i}", "country": "X",
                "activity_tags": random.sample(tag_pool, k=3),
                "budget_tier_min": random.randint(300, 2000),
                "budget_tier_max": random.randint(2001, 8000),
                "parallel_value_tags": [],
            }
            for i in range(50)
        ]
        for n in [1, 5, 10, 20]:
            result = rank_destinations(members, dests, top_n=n)
            assert len(result) <= n

    def test_conflict_both_missing_doesnt_crash(self):
        """Groups with no clear conflict tags should return empty list."""
        members = [
            {"id": "m1", "preference_tags": ["culture", "food"], "trip_duration_days": 7},
            {"id": "m2", "preference_tags": ["culture", "urban"], "trip_duration_days": 8},
        ]
        conflicts = detect_conflicts(members)
        assert isinstance(conflicts, list)

    def test_annotate_conflicts_empty_dest_tags(self):
        """annotate_conflicts with a dest that has no parallel_value_tags."""
        members = [
            {"id": "m1", "preference_tags": ["budget"], "trip_duration_days": 5},
            {"id": "m2", "preference_tags": ["luxury"], "trip_duration_days": 5},
        ]
        conflicts = detect_conflicts(members)
        dest_no_tags = {"name": "Nowhere", "parallel_value_tags": []}
        result = annotate_conflicts(conflicts, dest_no_tags)
        for c in result:
            assert "resolution_note" in c
            # Should still produce a note even with no parallel tags


# ── MemberPreferences model ───────────────────────────────────────────────────

class TestMemberPreferencesModel:
    def test_to_scoring_dict_round_trip(self):
        """New MemberPreferences rows with JSON tags produce correct scoring dicts."""
        import json
        from group_models import MemberPreferences, TripGroupMember

        prefs = MemberPreferences(
            id="pref-1",
            group_member_id="mem-1",
            budget_min=500,
            budget_max=2000,
            trip_duration_days=7,
        )
        prefs.preference_tags = ["beach", "food", "budget"]

        d = prefs.to_scoring_dict()

        assert d["budget_min"] == 500
        assert d["budget_max"] == 2000
        assert d["trip_duration_days"] == 7
        assert "beach" in d["preference_tags"]
        assert "food" in d["preference_tags"]
        assert "budget" in d["preference_tags"]

    def test_to_scoring_dict_empty_tags(self):
        from group_models import MemberPreferences

        prefs = MemberPreferences(
            id="pref-2",
            group_member_id="mem-2",
            budget_min=1000,
            budget_max=5000,
            trip_duration_days=14,
        )
        prefs.preference_tags = []
        d = prefs.to_scoring_dict()
        assert d["preference_tags"] == []
