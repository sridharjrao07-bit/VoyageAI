"""
Admin Groups Router — /api/admin/groups

Admin-only endpoints for auditing and replaying recommendation runs.
Currently uses simple admin flag check; integrate with a proper role system as needed.

Endpoints:
  GET /api/admin/groups/{group_id}/recommendations/{run_id}/replay
      Re-runs the algorithm on the stored preferences snapshot and returns
      the new result alongside the original for regression analysis.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from auth import get_current_user
from database import get_session
from engine.group_conflicts import annotate_conflicts, detect_conflicts
from engine.group_scoring import rank_destinations
from group_models import AlloraUser, GroupRecommendationRun, MemberPreferences, TripGroupMember
from models import Destination

router = APIRouter(prefix="/admin", tags=["Admin"])

ADMIN_USERNAMES = set(os.getenv("ADMIN_USERNAMES", "admin").split(","))
ALGORITHM_VERSION = "1.0.0"


async def get_admin_user(current_user: AlloraUser = Depends(get_current_user)) -> AlloraUser:
    """Dependency: checks that the current user is an admin."""
    if current_user.username not in ADMIN_USERNAMES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


def _dest_to_scoring_dict(dest: Destination) -> dict:
    import json
    try:
        activity_tags = json.loads(dest.activity_tags or "[]")
    except Exception:
        activity_tags = [t.strip() for t in (dest.activity_tags or "").split(",") if t.strip()]
    try:
        parallel_value_tags = json.loads(dest.parallel_value_tags or "[]")
    except Exception:
        parallel_value_tags = []

    return {
        "id": dest.id,
        "name": dest.name,
        "country": dest.country,
        "activity_tags": activity_tags,
        "budget_tier_min": dest.budget_tier_min or 0,
        "budget_tier_max": dest.budget_tier_max or 0,
        "parallel_value_tags": parallel_value_tags,
        "tags": dest.tags or "",
    }


@router.get(
    "/groups/{group_id}/recommendations/{run_id}/replay",
    summary="Replay a recommendation run",
)
async def replay_recommendation_run(
    group_id: str,
    run_id: str,
    _admin: AlloraUser = Depends(get_admin_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Re-runs the scoring algorithm on a stored run's preferences snapshot and returns
    BOTH the original result and the freshly-computed result for regression comparison.

    Uses the CURRENT destination catalog (not a snapshot), so score changes reflect
    updates to the destination data, not the member preferences.
    """
    # Load original run
    result = await session.execute(
        select(GroupRecommendationRun).where(
            and_(
                GroupRecommendationRun.id == run_id,
                GroupRecommendationRun.group_id == group_id,
            )
        )
    )
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Recommendation run not found")

    original_payload = run.result_payload

    # Rebuild full member preference dicts from the live DB
    # (We use the live preferences, not the anonymised snapshot, for accurate replay)
    members_result = await session.execute(
        select(TripGroupMember).where(
            and_(
                TripGroupMember.group_id == group_id,
                TripGroupMember.deleted_at == None,
            )
        )
    )
    members = members_result.scalars().all()

    scoring_members = []
    for m in members:
        pref_result = await session.execute(
            select(MemberPreferences).where(MemberPreferences.group_member_id == m.id)
        )
        prefs = pref_result.scalar_one_or_none()
        if prefs:
            d = prefs.to_scoring_dict()
            d["user_id"] = m.user_id
            d["display_name"] = m.user_id  # don't leak names in admin replay
            scoring_members.append(d)

    if not scoring_members:
        raise HTTPException(status_code=400, detail="No preferences available for replay")

    # Load destinations
    dest_result = await session.execute(
        select(Destination).where(Destination.deleted_at == None).limit(200)
    )
    destinations = [_dest_to_scoring_dict(d) for d in dest_result.scalars().all()]

    # Re-run scoring
    new_ranked = rank_destinations(scoring_members, destinations, top_n=10)
    new_conflicts = detect_conflicts(scoring_members)
    if new_ranked and new_conflicts:
        new_conflicts = annotate_conflicts(new_conflicts, new_ranked[0])

    new_payload = {
        "replayed_at": datetime.now(timezone.utc).isoformat(),
        "algorithm_version": ALGORITHM_VERSION,
        "original_algorithm_version": run.algorithm_version,
        "member_count": len(scoring_members),
        "conflicts_detected": new_conflicts,
        "destinations": new_ranked,
    }

    return {
        "run_id": run_id,
        "group_id": group_id,
        "original_run_at": run.run_at.isoformat() if run.run_at else None,
        "original": original_payload,
        "replay": new_payload,
        "note": (
            "Original used algorithm v{}. Current algorithm is v{}.".format(
                run.algorithm_version, ALGORITHM_VERSION
            )
        ),
    }
