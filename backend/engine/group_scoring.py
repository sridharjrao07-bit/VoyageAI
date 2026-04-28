"""
Fairness-Aware Group Scoring Engine

Implements the maximin criterion for group trip recommendations:
  - Each member is scored independently against each destination
  - The group score maximizes the MINIMUM member satisfaction (not the average)
  - A low-floor penalty de-prioritizes destinations that leave anyone severely underserved

This module has NO imports from FastAPI or SQLAlchemy — it operates on plain dicts
and can be tested and run in complete isolation.

Usage:
    from engine.group_scoring import rank_destinations

    ranked = rank_destinations(group_members, destinations, top_n=10)
"""
from __future__ import annotations

from statistics import mean


# ── Member × Destination Scoring ──────────────────────────────────────────────

def score_member_for_destination(member_prefs: dict, destination: dict) -> float:
    """
    Score a single member's compatibility with a single destination.

    Returns a float in [0.0, 1.0].

    member_prefs keys:
        preference_tags   list[str]     e.g. ["beach", "budget", "food"]
        budget_min        int           USD
        budget_max        int           USD

    destination keys:
        activity_tags     list[str]     e.g. ["beach", "culture", "food", "urban", "luxury"]
        budget_tier_min   int           USD per person (estimated low)
        budget_tier_max   int           USD per person (estimated high)
    """
    pref_tags: list[str] = member_prefs.get("preference_tags") or []
    dest_tags: list[str] = destination.get("activity_tags") or []

    # ── 1. Preference Match (weight 0.40) ─────────────────────────────────────
    overlap = len(set(pref_tags) & set(dest_tags))
    preference_score = overlap / max(len(pref_tags), 1)

    # ── 2. Budget Compatibility (weight 0.35) ──────────────────────────────────
    dest_min: float = float(destination.get("budget_tier_min") or 0)
    dest_max: float = float(destination.get("budget_tier_max") or dest_min)
    dest_mid: float = (dest_min + dest_max) / 2

    m_min: float = float(member_prefs.get("budget_min") or 300)
    m_max: float = float(member_prefs.get("budget_max") or 3000)
    member_mid: float = (m_min + m_max) / 2

    if dest_min <= 0:
        # No budget data → assume compatible
        budget_score = 1.0
    elif member_mid >= dest_min:
        if member_mid >= dest_mid:
            budget_score = 1.0
        else:
            denom = dest_mid - dest_min
            budget_score = (member_mid - dest_min) / denom if denom > 0 else 1.0
    else:
        shortfall_ratio = (dest_min - member_mid) / dest_min
        budget_score = max(0.0, 1.0 - shortfall_ratio * 2)

    # ── 3. Diversity Bonus (weight 0.25) ──────────────────────────────────────
    # Rewards destinations that serve multiple interest types (better compromise)
    diversity_score = min(1.0, len(dest_tags) / 5)

    # ── Weighted Sum ──────────────────────────────────────────────────────────
    raw = (preference_score * 0.40) + (budget_score * 0.35) + (diversity_score * 0.25)
    return max(0.0, min(1.0, raw))


# ── Group × Destination Scoring ───────────────────────────────────────────────

def score_destination_for_group(group_members: list[dict], destination: dict) -> dict:
    """
    Score a destination against the entire group using the fairness/maximin criterion.

    Returns:
        {
          fairness_score  float   primary ranking key
          maximin_score   float   worst member score (0.0 if group is empty)
          average_score   float
          per_member      list[{member_id, user_id, display_name, score}]
        }
    """
    if not group_members:
        return {
            "fairness_score": None,
            "maximin_score": None,
            "average_score": 0.0,
            "per_member": [],
        }

    member_scores = [score_member_for_destination(m, destination) for m in group_members]

    average_score = mean(member_scores)

    # Maximin (and fairness) are only defined for 2+ members — a comparative metric.
    if len(member_scores) < 2:
        return {
            "fairness_score": None,   # undefined for solo trips
            "maximin_score": None,
            "average_score": round(average_score, 4),
            "per_member": [
                {
                    "member_id": group_members[0].get("id"),
                    "user_id": group_members[0].get("user_id"),
                    "display_name": group_members[0].get("display_name", "Member 1"),
                    "score": round(member_scores[0], 4),
                }
            ],
        }

    maximin_score = min(member_scores)

    fairness_score = (maximin_score * 0.65) + (average_score * 0.35)

    # Low-floor penalty: if anyone scores below 0.30, apply 20% penalty
    if maximin_score < 0.30:
        fairness_score *= 0.80

    per_member = [
        {
            "member_id": m.get("id"),
            "user_id": m.get("user_id"),
            "display_name": m.get("display_name", f"Member {i+1}"),
            "score": round(s, 4),
        }
        for i, (m, s) in enumerate(zip(group_members, member_scores))
    ]

    return {
        "fairness_score": round(max(0.0, min(1.0, fairness_score)), 4),
        "maximin_score": round(maximin_score, 4),
        "average_score": round(average_score, 4),
        "per_member": per_member,
    }


# ── Ranking ────────────────────────────────────────────────────────────────────

def rank_destinations(
    group_members: list[dict],
    destinations: list[dict],
    top_n: int = 10,
) -> list[dict]:
    """
    Score every destination for the group and return the top-N sorted by fairness_score.

    Each returned item is the original destination dict merged with the scoring result,
    plus a 'rank' field (1-indexed).

    Returns an empty list if destinations is empty — never raises.
    """
    if not destinations:
        return []

    scored = []
    for dest in destinations:
        group_result = score_destination_for_group(group_members, dest)
        scored.append({**dest, **group_result})

    # Solo trip: fairness_score is None — fall back to average_score for ranking
    scored.sort(key=lambda x: x["fairness_score"] if x["fairness_score"] is not None else x["average_score"], reverse=True)

    results = scored[:top_n]
    for i, item in enumerate(results):
        item["rank"] = i + 1

    return results
