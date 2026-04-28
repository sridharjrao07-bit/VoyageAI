"""
Hybrid Recommendation Engine  v2 — Data Quality & Diversity Agent
Blends: Content-Based (50%) + Collaborative (30%) + Popularity (20%)

Upgrades in v2:
  - Semantic Intent: tags are expanded before scoring (adventure → climbing/rafting…)
  - 40% Discovery quota: guaranteed fraction of low-footprint novelty picks
  - Weather penalty: destinations with severe weather are down-ranked
  - Delta XAI: each result explains WHY it is fresh vs what the user has seen
  - Anti-repetition: seen_ids strictly excluded before any scoring
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from engine.content_based import score_by_content
from engine.collaborative import score_by_collaborative, get_popularity_scores
from engine.data_loader import get_destinations, get_user_by_id
from engine.tag_expander import expand_tags

# Weights for the hybrid blend
W_CONTENT = 0.50
W_COLLAB  = 0.30
W_POPULAR = 0.20

# Fraction of results that MUST be discoveries (low-footprint / novelty)
DISCOVERY_FRACTION = 0.40   # 40% as per spec

# Weather severity keywords that trigger a score penalty
_SEVERE_WEATHER_KEYWORDS = {
    "thunderstorm", "tornado", "hurricane", "typhoon", "blizzard",
    "extreme", "flood", "hail", "storm", "cyclone", "warning", "alert",
}
WEATHER_PENALTY = 0.25   # subtract this from score on severe weather


def _normalize(scores: dict) -> dict:
    if not scores:
        return {}
    vals = np.array(list(scores.values()), dtype=float)
    min_v, max_v = vals.min(), vals.max()
    if max_v - min_v < 1e-9:
        return {k: 0.5 for k in scores}
    return {k: (v - min_v) / (max_v - min_v) for k, v in scores.items()}


def _is_severe_weather(weather_desc: str) -> bool:
    desc_lower = (weather_desc or "").lower()
    return any(kw in desc_lower for kw in _SEVERE_WEATHER_KEYWORDS)


def _generate_xai(dest_row, user_tags: list[str], matched_tags: list[str],
                  is_collaborative: bool, is_popular: bool, score: float,
                  is_novelty: bool, seen_names: list[str]) -> str:
    """
    Generates a 'Why recommended' explanation that also articulates the Delta —
    why this place is a FRESH alternative to what the user has already seen.
    """
    parts = []

    if matched_tags:
        parts.append(f"Matches your interest in {', '.join(matched_tags[:3])}")

    if is_collaborative:
        parts.append("travellers with similar tastes loved it")

    if is_popular:
        parts.append(f"highly rated at {dest_row['avg_rating']}\u2605")

    budget_match = ""
    if "budget" in user_tags or "backpacker" in user_tags:
        if dest_row["avg_cost_usd"] < 800:
            budget_match = "fits your budget perfectly"
    elif "luxury" in user_tags:
        if dest_row["avg_cost_usd"] > 2000:
            budget_match = "matches your taste for luxury"
    if budget_match:
        parts.append(budget_match)

    # Delta: explain freshness vs seen destinations
    if is_novelty:
        parts.append(
            "a hidden gem — rarely recommended, giving you a genuinely unique experience"
            + (f" compared to the popular {seen_names[0]}" if seen_names else "")
        )
    elif seen_names:
        parts.append(f"a fresh alternative to {seen_names[0]} that you've already discovered")

    if not parts:
        parts.append(f"a top-rated {dest_row['climate']} destination")

    return " \u2022 ".join(parts[:4]).capitalize() + "."


def _fetch_weather_sync(lat: float, lon: float) -> str | None:
    """
    Synchronously fetch current weather description for scoring.
    Uses httpx sync client to avoid conflicting with uvicorn's event loop.
    Returns weather description string or None on failure.
    """
    import os
    import httpx
    owm_key = os.getenv("OPENWEATHERMAP_API_KEY", "")
    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={"lat": lat, "lon": lon, "appid": owm_key, "units": "metric"},
            )
            if resp.status_code == 200:
                weather_list = resp.json().get("weather", [{}])
                return weather_list[0].get("description", "")
    except Exception:
        pass
    return None



def recommend(
    user_id: str,
    tags: list[str],
    budget_usd: float,
    accessibility_required: bool,
    top_n: int = 10,
    feedback_overrides: dict = None,
    seen_ids: list[str] = None,
    weather_aware: bool = False,
    surprise_mode: bool = False,
) -> list[dict]:
    """
    Main recommendation function — Data Quality & Diversity Agent v2.

    Parameters
    ----------
    seen_ids     : Destination IDs already shown. Strictly excluded.
    weather_aware: If True, down-rank destinations with severe weather alerts.
                   Adds latency (1 OWM call per candidate). Use selectively.
    surprise_mode: If True, bypass content-based filter and popularity entirely.
                   Forces 100% novelty picks (bottom 30th percentile popularity).
    """
    destinations = get_destinations()
    if destinations is None:
        return []

    seen_set = set(seen_ids or [])

    # ── Surprise Mode: override weights to surfacing only hidden gems ──────────
    if surprise_mode:
        # Ignore content/collab entirely; rank purely by inverse popularity
        discovery_fraction_override = 1.0  # 100% hidden gems
        w_content_eff = 0.0
        w_collab_eff  = 0.0
        w_popular_eff = 1.0   # We'll invert this below
    else:
        discovery_fraction_override = DISCOVERY_FRACTION
        w_content_eff = None  # resolved later per cold-start logic
        w_collab_eff  = None
        w_popular_eff = None

    # ── Semantic Intent Expansion ────────────────────────────────────────────
    expanded_tags = expand_tags(tags)

    # ── Scoring ──────────────────────────────────────────────────────────────
    content_raw  = score_by_content(expanded_tags)   # uses expanded synonyms
    collab_raw   = score_by_collaborative(user_id)
    popular_raw  = get_popularity_scores()

    is_cold_start = len(collab_raw) == 0
    if surprise_mode:
        # Invert popularity: lowest-popularity items get highest score
        inv_popular_raw = {k: (1.0 - v) if isinstance(v, float) else v for k, v in popular_raw.items()}
        w_c = 0.0
        w_k = 0.0
        w_p = 1.0
        score_source = inv_popular_raw
    else:
        w_c = 0.70 if is_cold_start else W_CONTENT
        w_k = 0.00 if is_cold_start else W_COLLAB
        w_p = 0.30 if is_cold_start else W_POPULAR
        score_source = popular_raw

    content_norm = _normalize(content_raw)
    collab_norm  = _normalize(collab_raw)
    popular_norm = _normalize(score_source if surprise_mode else popular_raw)

    all_ids = destinations["id"].tolist()
    hybrid_scores: dict[str, float] = {}
    for dest_id in all_ids:
        c = content_norm.get(dest_id, 0.0)
        k = collab_norm.get(dest_id, 0.0)
        p = popular_norm.get(dest_id, 0.0)
        score = w_c * c + w_k * k + w_p * p
        if feedback_overrides:
            score += feedback_overrides.get(dest_id, 0.0)
        hybrid_scores[dest_id] = max(0.0, score)

    # ── Discovery threshold (40% of results must be "Discoveries") ───────────
    pop_values = list(popular_norm.values())
    # Novelty = bottom 40% by popularity → they are high-quality but low-footprint
    novelty_threshold = float(np.percentile(pop_values, 40)) if pop_values else 0.3

    dest_index   = destinations.set_index("id")
    regular_pool: list[dict] = []
    novelty_pool: list[dict] = []
    seen_names:   set[str]   = set()

    for dest_id, score in sorted(hybrid_scores.items(), key=lambda x: -x[1]):
        if len(regular_pool) + len(novelty_pool) >= top_n * 5:
            break
        if dest_id not in dest_index.index:
            continue

        # ── Anti-repetition: strict exclusion ────────────────────────────────
        if dest_id in seen_set:
            continue

        row = dest_index.loc[dest_id]

        if str(row["name"]) in seen_names:
            continue

        # Budget + accessibility filters
        if budget_usd > 0 and row["avg_cost_usd"] > budget_usd * 1.3:
            continue
        if accessibility_required:
            val = str(row.get("accessibility", "false")).lower()
            if val not in ("true", "1", "yes"):
                continue

        # ── Contextual Safety: weather down-ranking ───────────────────────────
        weather_penalty_applied = False
        weather_note = ""
        if weather_aware:
            weather_desc = _fetch_weather_sync(
                float(row["latitude"]), float(row["longitude"])
            )
            if weather_desc and _is_severe_weather(weather_desc):
                score = max(0.0, score - WEATHER_PENALTY)
                weather_penalty_applied = True
                weather_note = f"⚠️ Live weather alert: {weather_desc}."

        # XAI
        dest_tags  = set(str(row.get("tags", "")).replace(",", " ").split())
        user_tag_s = set(expanded_tags)
        matched    = list(dest_tags & user_tag_s)
        is_novelty = popular_norm.get(dest_id, 0.0) <= novelty_threshold

        # Recent seen names for delta explanation
        recent_seen_names = [
            dest_index.loc[s]["name"]
            for s in list(seen_set)[:2]
            if s in dest_index.index
        ]

        xai = _generate_xai(
            row, expanded_tags, matched,
            is_collaborative=dest_id in collab_norm,
            is_popular=popular_norm.get(dest_id, 0) > 0.5,
            score=score,
            is_novelty=is_novelty,
            seen_names=recent_seen_names,
        )
        if weather_note:
            xai = weather_note + " " + xai

        entry = {
            "id":            dest_id,
            "name":          row["name"],
            "country":       row["country"],
            "continent":     row["continent"],
            "tags":          [t.strip() for t in str(row["tags"]).split(",")],
            "avg_cost_usd":  int(row["avg_cost_usd"]),
            "avg_rating":    float(row["avg_rating"]),
            "climate":       row["climate"],
            "best_season":   row["best_season"],
            "description":   row["description"],
            "accessibility": str(row["accessibility"]).lower() == "true",
            "latitude":      float(row["latitude"]),
            "longitude":     float(row["longitude"]),
            "xid":           str(row.get("xid", "")),
            "score":         round(score, 4),
            "xai_snippet":   xai,
            "is_cold_start": bool(is_cold_start),
            "is_novelty":    bool(is_novelty),
            "is_discovery":  bool(is_novelty),               # alias for spec compatibility
            "weather_flagged": bool(weather_penalty_applied),
            "expanded_tags_used": expanded_tags[:8],   # transparency: show expansion
        }

        if is_novelty:
            novelty_pool.append(entry)
        else:
            regular_pool.append(entry)

        seen_names.add(str(row["name"]))

    # ── 40% Discovery Injection (or 100% in surprise mode) ───────────────────
    effective_discovery_fraction = 1.0 if surprise_mode else DISCOVERY_FRACTION
    n_discoveries = max(1, round(top_n * effective_discovery_fraction))
    n_discoveries = min(n_discoveries, len(novelty_pool))
    n_regular     = top_n - n_discoveries
    n_regular     = min(n_regular, len(regular_pool))

    discovery_picks = novelty_pool[:n_discoveries]
    regular_picks   = regular_pool[:n_regular]

    # Interleave: 1st slot discovery, then regulars, then another discovery
    final: list[dict] = []
    d_iter = iter(discovery_picks)
    r_iter = iter(regular_picks)

    d1 = next(d_iter, None)
    if d1:
        final.append(d1)

    for i, r in enumerate(r_iter):
        final.append(r)
        if i == 2:          # inject 2nd discovery after 3rd regular
            d2 = next(d_iter, None)
            if d2:
                final.append(d2)

    # Fill any remaining discovery slots at the end
    final.extend(d_iter)
    final.extend(r_iter)

    return final[:top_n]
