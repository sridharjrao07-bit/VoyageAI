"""
Groups Router — /api/groups

All endpoints require authentication (Bearer JWT).
Members can only access their own groups.
Owners have write access (add/remove members, change group status).

Endpoints:
  POST   /api/groups                                          create group
  POST   /api/groups/{group_id}/members                       add member (owner)
  DELETE /api/groups/{group_id}/members/{user_id}            remove member
  PUT    /api/groups/{group_id}/preferences                   submit my preferences
  GET    /api/groups/{group_id}/preferences/status            who has submitted
  POST   /api/groups/{group_id}/recommend                     run recommendation
  GET    /api/groups/{group_id}/recommendations/{run_id}      fetch past run
  GET    /api/groups                                          list my groups
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from auth import get_current_user
from database import get_session
from engine.group_conflicts import annotate_conflicts, detect_conflicts
from engine.group_scoring import rank_destinations
from group_models import (
    AlloraUser,
    GroupRecommendationRun,
    MemberPreferences,
    TripGroup,
    TripGroupMember,
)
from models import Destination

router = APIRouter(prefix="/groups", tags=["Groups"])

ALGORITHM_VERSION = "1.0.0"


# ── Request / Response Schemas ─────────────────────────────────────────────────

class CreateGroupRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=256)
    invited_user_ids: List[str] = Field(default=[])


class AddMemberRequest(BaseModel):
    user_id: str


class PreferencesRequest(BaseModel):
    preference_tags: List[str] = Field(..., description="Max 3 tags from the standard set")
    budget_min: int = Field(..., ge=300, le=10000)
    budget_max: int = Field(..., ge=300, le=10000)
    trip_duration_days: int = Field(..., ge=1, le=60)
    region_preference: Optional[str] = None


# ── Helpers ────────────────────────────────────────────────────────────────────

async def _get_membership(
    group_id: str, user_id: str, session: AsyncSession
) -> TripGroupMember:
    """Return membership or raise 403."""
    result = await session.execute(
        select(TripGroupMember).where(
            and_(
                TripGroupMember.group_id == group_id,
                TripGroupMember.user_id == user_id,
                TripGroupMember.deleted_at == None,
            )
        )
    )
    membership = result.scalar_one_or_none()
    if not membership:
        raise HTTPException(status_code=403, detail="You are not a member of this group")
    return membership


async def _get_group_with_members(group_id: str, session: AsyncSession) -> TripGroup:
    result = await session.execute(
        select(TripGroup)
        .options(
            selectinload(TripGroup.members)
            .selectinload(TripGroupMember.user),
            selectinload(TripGroup.members)
            .selectinload(TripGroupMember.preferences),
        )
        .where(and_(TripGroup.id == group_id, TripGroup.deleted_at == None))
    )
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return group


def _member_to_dict(m: TripGroupMember) -> dict:
    return {
        "id": m.id,
        "user_id": m.user_id,
        "display_name": m.user.display_name if m.user else m.user_id,
        "username": m.user.username if m.user else "",
        "avatar_emoji": m.user.avatar_emoji if m.user else "🧳",
        "role": m.role,
        "joined_at": m.joined_at.isoformat() if m.joined_at else None,
        "preferences_submitted": m.preferences_submitted_at is not None,
    }


def _dest_to_scoring_dict(dest: Destination) -> dict:
    """Convert ORM Destination to plain dict for the scoring engine."""
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
        "region": getattr(dest, "continent", ""),
        "activity_tags": activity_tags,
        "budget_tier_min": dest.budget_tier_min or 0,
        "budget_tier_max": dest.budget_tier_max or 0,
        "parallel_value_tags": parallel_value_tags,
        "tags": dest.tags or "",
        "avg_cost_usd": dest.avg_cost_usd or 0,
    }


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.get("", summary="List my groups")
async def list_my_groups(
    current_user: AlloraUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """List all trip groups the authenticated user belongs to."""
    result = await session.execute(
        select(TripGroupMember)
        .options(
            selectinload(TripGroupMember.group),
            selectinload(TripGroupMember.group).selectinload(TripGroup.members),
        )
        .where(
            and_(
                TripGroupMember.user_id == current_user.id,
                TripGroupMember.deleted_at == None,
            )
        )
    )
    memberships = result.scalars().all()

    groups = []
    for m in memberships:
        g = m.group
        if g and not g.deleted_at:
            active_members = [mb for mb in g.members if not mb.deleted_at]
            groups.append({
                "id": g.id,
                "name": g.name,
                "status": g.status,
                "created_at": g.created_at.isoformat() if g.created_at else None,
                "member_count": len(active_members),
                "my_role": m.role,
                "preferences_submitted": m.preferences_submitted_at is not None,
            })

    return {"total": len(groups), "groups": groups}


@router.post("", status_code=status.HTTP_201_CREATED, summary="Create a trip group")
async def create_group(
    req: CreateGroupRequest,
    current_user: AlloraUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Create a new trip group and optionally invite members."""
    group_id = str(uuid.uuid4())
    group = TripGroup(
        id=group_id,
        name=req.name,
        created_by=current_user.id,
        status="active",
    )
    session.add(group)

    # Add creator as owner
    owner_member = TripGroupMember(
        id=str(uuid.uuid4()),
        group_id=group_id,
        user_id=current_user.id,
        role="owner",
    )
    session.add(owner_member)

    # Add invited members (skip non-existent users silently)
    added_ids = [current_user.id]
    for uid in req.invited_user_ids:
        if uid in added_ids:
            continue
        user_check = await session.execute(select(AlloraUser).where(AlloraUser.id == uid))
        if user_check.scalar_one_or_none():
            session.add(TripGroupMember(
                id=str(uuid.uuid4()),
                group_id=group_id,
                user_id=uid,
                role="member",
            ))
            added_ids.append(uid)

    await session.flush()
    return {
        "id": group_id,
        "name": group.name,
        "status": group.status,
        "created_by": current_user.id,
        "member_count": len(added_ids),
        "message": f"Group '{req.name}' created successfully",
    }


@router.get("/{group_id}", summary="Get group details")
async def get_group(
    group_id: str,
    current_user: AlloraUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get group details (members must be a member)."""
    await _get_membership(group_id, current_user.id, session)
    group = await _get_group_with_members(group_id, session)
    active_members = [m for m in group.members if not m.deleted_at]

    return {
        "id": group.id,
        "name": group.name,
        "status": group.status,
        "created_by": group.created_by,
        "created_at": group.created_at.isoformat() if group.created_at else None,
        "members": [_member_to_dict(m) for m in active_members],
    }


@router.post("/{group_id}/members", status_code=status.HTTP_201_CREATED, summary="Add member")
async def add_member(
    group_id: str,
    req: AddMemberRequest,
    current_user: AlloraUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Add a member to the group (owner only)."""
    membership = await _get_membership(group_id, current_user.id, session)
    if membership.role != "owner":
        raise HTTPException(status_code=403, detail="Only the group owner can add members")

    # Verify invitee exists
    user_check = await session.execute(
        select(AlloraUser).where(AlloraUser.id == req.user_id)
    )
    if not user_check.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="User not found")

    # Check not already a member
    existing = await session.execute(
        select(TripGroupMember).where(
            and_(
                TripGroupMember.group_id == group_id,
                TripGroupMember.user_id == req.user_id,
                TripGroupMember.deleted_at == None,
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="User is already a member")

    new_member = TripGroupMember(
        id=str(uuid.uuid4()),
        group_id=group_id,
        user_id=req.user_id,
        role="member",
    )
    session.add(new_member)
    await session.flush()

    return {"message": "Member added", "user_id": req.user_id, "role": "member"}


@router.delete("/{group_id}/members/{target_user_id}", summary="Remove member")
async def remove_member(
    group_id: str,
    target_user_id: str,
    current_user: AlloraUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Remove a member (owner can remove anyone; members can only remove themselves)."""
    my_membership = await _get_membership(group_id, current_user.id, session)

    is_self = target_user_id == current_user.id
    if not is_self and my_membership.role != "owner":
        raise HTTPException(status_code=403, detail="Only owners can remove other members")

    # Find target
    target_result = await session.execute(
        select(TripGroupMember).where(
            and_(
                TripGroupMember.group_id == group_id,
                TripGroupMember.user_id == target_user_id,
                TripGroupMember.deleted_at == None,
            )
        )
    )
    target = target_result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="Member not found")

    # Soft delete
    target.deleted_at = datetime.now(timezone.utc)
    await session.flush()

    return {"message": "Member removed", "user_id": target_user_id}


@router.put("/{group_id}/preferences", summary="Submit preferences")
async def submit_preferences(
    group_id: str,
    req: PreferencesRequest,
    current_user: AlloraUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Save or update the authenticated user's preferences for this group."""
    membership = await _get_membership(group_id, current_user.id, session)

    # Enforce max 3 tags
    tags = req.preference_tags[:3]
    if req.budget_min > req.budget_max:
        raise HTTPException(status_code=400, detail="budget_min must be ≤ budget_max")

    # Upsert preferences (one row per membership)
    pref_result = await session.execute(
        select(MemberPreferences).where(
            MemberPreferences.group_member_id == membership.id
        )
    )
    prefs = pref_result.scalar_one_or_none()

    if prefs:
        prefs.preference_tags = tags
        prefs.budget_min = req.budget_min
        prefs.budget_max = req.budget_max
        prefs.trip_duration_days = req.trip_duration_days
        prefs.region_preference = req.region_preference
        prefs.submitted_at = datetime.now(timezone.utc)
    else:
        prefs = MemberPreferences(
            id=str(uuid.uuid4()),
            group_member_id=membership.id,
            budget_min=req.budget_min,
            budget_max=req.budget_max,
            trip_duration_days=req.trip_duration_days,
            region_preference=req.region_preference,
        )
        prefs.preference_tags = tags
        session.add(prefs)

    membership.preferences_submitted_at = datetime.now(timezone.utc)
    await session.flush()

    return {
        "message": "Preferences saved",
        "group_id": group_id,
        "preference_tags": tags,
        "budget_min": req.budget_min,
        "budget_max": req.budget_max,
        "trip_duration_days": req.trip_duration_days,
        "region_preference": req.region_preference,
    }


@router.get("/{group_id}/preferences/status", summary="Get preference submission status")
async def preferences_status(
    group_id: str,
    current_user: AlloraUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Return which members have and haven't submitted preferences yet."""
    await _get_membership(group_id, current_user.id, session)
    group = await _get_group_with_members(group_id, session)
    active_members = [m for m in group.members if not m.deleted_at]

    submitted, pending = [], []
    for m in active_members:
        info = {
            "user_id": m.user_id,
            "display_name": m.user.display_name if m.user else m.user_id,
            "avatar_emoji": m.user.avatar_emoji if m.user else "🧳",
        }
        if m.preferences_submitted_at:
            submitted.append(info)
        else:
            pending.append(info)

    return {
        "group_id": group_id,
        "total_members": len(active_members),
        "submitted_count": len(submitted),
        "pending_count": len(pending),
        "all_ready": len(pending) == 0,
        "submitted": submitted,
        "pending": pending,
    }


@router.post("/{group_id}/recommend", summary="Run group recommendation")
async def run_recommendation(
    group_id: str,
    current_user: AlloraUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Run a fairness-aware recommendation for the group.
    Requires all members to have submitted preferences.
    Stores the result in group_recommendation_runs.
    """
    await _get_membership(group_id, current_user.id, session)
    group = await _get_group_with_members(group_id, session)
    active_members = [m for m in group.members if not m.deleted_at]

    # Check all members have submitted
    pending = [m for m in active_members if not m.preferences_submitted_at]
    if pending:
        pending_names = [
            m.user.display_name if m.user else m.user_id for m in pending
        ]
        raise HTTPException(
            status_code=400,
            detail=f"Waiting for preferences from: {', '.join(pending_names)}",
        )

    # Build member scoring dicts (latest preferences only, no raw tags exposed cross-member)
    scoring_members = []
    for m in active_members:
        if m.preferences:
            d = m.preferences.to_scoring_dict()
            d["user_id"] = m.user_id
            d["display_name"] = m.user.display_name if m.user else m.user_id
            scoring_members.append(d)

    if not scoring_members:
        raise HTTPException(status_code=400, detail="No preference data found for members")

    # Load destination candidates (those with group-enriched data)
    dest_result = await session.execute(
        select(Destination).where(
            and_(
                Destination.deleted_at == None,
                Destination.budget_tier_min != None,
                Destination.budget_tier_min > 0,
            )
        ).limit(200)
    )
    destinations_orm = dest_result.scalars().all()

    if not destinations_orm:
        # Fallback: use all destinations even without budget_tier data
        dest_result = await session.execute(
            select(Destination).where(Destination.deleted_at == None).limit(200)
        )
        destinations_orm = dest_result.scalars().all()

    destinations = [_dest_to_scoring_dict(d) for d in destinations_orm]

    # Run scoring
    ranked = rank_destinations(scoring_members, destinations, top_n=10)

    # Run conflict detection
    raw_conflicts = detect_conflicts(scoring_members)
    conflicts = []
    if ranked and raw_conflicts:
        conflicts = annotate_conflicts(raw_conflicts, ranked[0])
    elif raw_conflicts:
        conflicts = [
            {**c, "resolution_note": "No destinations matched to bridge this conflict."}
            for c in raw_conflicts
        ]

    # Build per-member score response (scores OK, raw preferences NOT exposed)
    result_destinations = []
    for dest in ranked:
        member_scores = []
        for pm in dest.get("per_member", []):
            score_pct = pm["score"] * 100
            member_scores.append({
                "user_id": pm["user_id"],
                "display_name": pm["display_name"],
                "score": pm["score"],
                "score_pct": round(score_pct, 1),
                "tier": "green" if score_pct >= 60 else ("amber" if score_pct >= 40 else "red"),
            })

        result_destinations.append({
            "destination_id": dest["id"],
            "name": dest["name"],
            "country": dest["country"],
            "fairness_score": dest["fairness_score"],
            "maximin_score": dest["maximin_score"],
            "average_score": dest["average_score"],
            "rank": dest["rank"],
            "tags": dest.get("tags", ""),
            "activity_tags": dest.get("activity_tags", []),
            "budget_range": {
                "min": dest.get("budget_tier_min") or None,
                "max": dest.get("budget_tier_max") or None,
            },
            "member_scores": member_scores,
        })

    result_payload = {
        "group_id": group_id,
        "algorithm_version": ALGORITHM_VERSION,
        "scored_at": datetime.now(timezone.utc).isoformat(),
        "member_count": len(active_members),
        "conflicts_detected": conflicts,
        "destinations": result_destinations,
        # Store anonymised snapshot of preferences for audit/replay
        "preferences_snapshot": [
            {
                "member_id": m["id"],
                "budget_min": m["budget_min"],
                "budget_max": m["budget_max"],
                "trip_duration_days": m["trip_duration_days"],
                "tag_count": len(m["preference_tags"]),
            }
            for m in scoring_members
        ],
    }

    # Persist the run
    run_id = str(uuid.uuid4())
    run = GroupRecommendationRun(
        id=run_id,
        group_id=group_id,
        algorithm_version=ALGORITHM_VERSION,
    )
    run.result_payload = result_payload
    session.add(run)
    await session.flush()

    return {
        "run_id": run_id,
        "conflicts_detected": conflicts,
        "destinations": result_destinations,
    }


@router.get("/{group_id}/recommendations/{run_id}", summary="Fetch past recommendation run")
async def get_recommendation_run(
    group_id: str,
    run_id: str,
    current_user: AlloraUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Retrieve a previously saved recommendation run by ID."""
    await _get_membership(group_id, current_user.id, session)

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

    payload = run.result_payload
    return {
        "run_id": run_id,
        "group_id": group_id,
        "run_at": run.run_at.isoformat() if run.run_at else None,
        "algorithm_version": run.algorithm_version,
        **payload,
    }
