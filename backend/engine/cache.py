"""
Candidate Cache — Performance Feature 4
A simple in-process TTL dict cache for recommender candidates.

Key: (sorted_tags_hash, budget_usd, weather_aware, surprise_mode)
TTL: 5 minutes (300 seconds)

This avoids re-calling the Grok LLM for identical (or near-identical)
queries within a short time window, cutting P95 latency significantly.
"""
from __future__ import annotations
import hashlib
import time
from typing import Any, Optional

_TTL_SECONDS = 300  # 5 minutes


class RecommendationCache:
    def __init__(self):
        self._store: dict[str, tuple[float, Any]] = {}  # key → (expires_at, value)
        self._hits = 0
        self._misses = 0

    # ── Public API ─────────────────────────────────────────────────────────────

    @staticmethod
    def make_key(
        tags: list[str],
        budget_usd: float,
        weather_aware: bool,
        surprise_mode: bool,
        include_flights: bool = False,
        currency_preference: str = "INR"
    ) -> str:
        """Deterministic cache key from sorted tags + scalar params."""
        tag_blob = ",".join(sorted(tags))
        raw = f"{tag_blob}|{budget_usd:.0f}|{weather_aware}|{surprise_mode}|{include_flights}|{currency_preference}"
        return hashlib.md5(raw.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """Return cached value if it exists and hasn't expired, else None."""
        entry = self._store.get(key)
        if entry is None:
            self._misses += 1
            return None
        expires_at, value = entry
        if time.monotonic() > expires_at:
            del self._store[key]
            self._misses += 1
            return None
        self._hits += 1
        return value

    def set(self, key: str, value: Any) -> None:
        """Store a value with a TTL from now."""
        self._store[key] = (time.monotonic() + _TTL_SECONDS, value)
        # Prune entries that have already expired to avoid unbounded growth
        self._prune()

    def stats(self) -> dict:
        """Return cache health statistics."""
        total = self._hits + self._misses
        return {
            "hits": self._hits,
            "misses": self._misses,
            "total_requests": total,
            "hit_rate_pct": round(self._hits / total * 100, 1) if total else 0.0,
            "active_entries": len(self._store),
            "ttl_seconds": _TTL_SECONDS,
        }

    def clear(self) -> None:
        self._store.clear()
        self._hits = 0
        self._misses = 0

    # ── Internal ───────────────────────────────────────────────────────────────

    def _prune(self) -> None:
        now = time.monotonic()
        stale = [k for k, (exp, _) in self._store.items() if now > exp]
        for k in stale:
            del self._store[k]


# Module-level singleton used by main.py
recommendation_cache = RecommendationCache()
