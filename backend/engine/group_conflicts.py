"""
Group Preference Conflict Detection

Detects opposing preference signals within a trip group and generates
resolution notes that explain why the top-ranked destination is a good compromise.

Conflict pairs checked:
  "budget"    vs "luxury"      → Budget vs Luxury
  "adventure" vs "relaxation"  → Adventure vs Relaxation
  "remote"    vs "urban"       → Remote vs Urban
  "short-trip" / short duration vs "extended" / long duration → Trip Length Conflict

Resolution notes are generated from the destination's parallel_value_tags field,
which describes what both budget and luxury (or adventure and relaxation, etc.) 
travelers can find at that destination.
"""
from __future__ import annotations

from statistics import variance

# ── Conflict Taxonomy ──────────────────────────────────────────────────────────

CONFLICT_PAIRS: list[tuple[str, str, str]] = [
    ("budget",    "luxury",      "Budget vs Luxury"),
    ("adventure", "relaxation",  "Adventure vs Relaxation"),
    ("remote",    "urban",       "Remote vs Urban"),
]

# Template resolution notes keyed by conflict type.
# The destination name and parallel_value_tags are injected at runtime.
_RESOLUTION_TEMPLATES: dict[str, str] = {
    "budget_vs_luxury": (
        "{name} caters to both ends of the spectrum: budget travelers can find "
        "{budget_options}, while luxury seekers enjoy {luxury_options}."
    ),
    "adventure_vs_relaxation": (
        "{name} offers thrilling {adventure_options} for the adventurous, "
        "alongside peaceful {relax_options} for those who want to unwind."
    ),
    "remote_vs_urban": (
        "{name} blends city energy {urban_options} with nearby escapes into "
        "nature {remote_options} — perfect for mixed groups."
    ),
    "duration_mismatch": (
        "{name} is a destination that rewards both quick visits and longer stays, "
        "so the group can agree on any trip length that works."
    ),
}

# Tag-to-human-readable option mapping for resolution note generation
_TAG_PHRASES: dict[str, str] = {
    "hostel":         "budget hostels and guesthouses",
    "backpacker":     "affordable backpacker digs",
    "local-market":   "bustling local markets and street food",
    "street-food":    "vibrant street food scenes",
    "boutique":       "boutique hotels",
    "michelin":       "Michelin-starred dining",
    "fine-dining":    "fine-dining restaurants",
    "luxury-resort":  "luxury resorts and spas",
    "hiking":         "epic hiking trails",
    "surfing":        "world-class surfing",
    "trekking":       "multi-day trekking expeditions",
    "spa":            "serene spa retreats",
    "beach":          "tranquil beaches",
    "yoga":           "yoga and wellness retreats",
    "city-life":      "vibrant city neighbourhoods",
    "nightlife":      "lively nightlife districts",
    "day-trip":       "scenic day trips to the countryside",
    "nature":         "untouched natural landscapes",
}

# Which tags belong to each side of a conflict
_CONFLICT_TAG_MAP: dict[str, dict[str, list[str]]] = {
    "budget_vs_luxury": {
        "budget":  ["hostel", "backpacker", "local-market", "street-food"],
        "luxury":  ["boutique", "michelin", "fine-dining", "luxury-resort"],
    },
    "adventure_vs_relaxation": {
        "adventure": ["hiking", "surfing", "trekking"],
        "relax":     ["spa", "beach", "yoga"],
    },
    "remote_vs_urban": {
        "urban":  ["city-life", "nightlife"],
        "remote": ["day-trip", "nature"],
    },
}


# ── Conflict Detection ─────────────────────────────────────────────────────────

def detect_conflicts(group_members: list[dict]) -> list[dict]:
    """
    Analyse the group's collective preference tags and trip duration to find
    opposing signals.

    group_members list items must contain:
        preference_tags     list[str]
        trip_duration_days  int (optional)

    Returns list of:
        { type: str, label: str }
    """
    # Collect all tags across all members + per-member tag sets
    all_tags: set[str] = set()
    for m in group_members:
        for tag in m.get("preference_tags") or []:
            all_tags.add(tag.lower())

    conflicts: list[dict] = []

    # Tag-based conflict pairs
    for tag_a, tag_b, label in CONFLICT_PAIRS:
        if tag_a in all_tags and tag_b in all_tags:
            conflict_type = f"{tag_a}_vs_{tag_b}"
            conflicts.append({"type": conflict_type, "label": label})

    # Duration-based conflict (variance > 4-day gap between shortest and longest)
    durations = [
        int(m["trip_duration_days"])
        for m in group_members
        if m.get("trip_duration_days") and int(m.get("trip_duration_days", 0)) > 0
    ]
    if len(durations) >= 2 and (max(durations) - min(durations)) > 4:
        conflicts.append({"type": "duration_mismatch", "label": "Trip Length Conflict"})

    return conflicts


# ── Resolution Note Generation ─────────────────────────────────────────────────

def generate_resolution_note(conflict_type: str, destination: dict) -> str:
    """
    Generate a human-readable note explaining why this destination bridges
    the detected conflict, using the destination's parallel_value_tags.

    destination keys:
        name                str
        parallel_value_tags list[str]  — tags describing dual-appeal options
    """
    name: str = destination.get("name", "This destination")
    pvt: list[str] = [t.lower() for t in (destination.get("parallel_value_tags") or [])]

    template = _RESOLUTION_TEMPLATES.get(conflict_type)
    if not template:
        return f"{name} offers something for everyone in the group."

    tag_map = _CONFLICT_TAG_MAP.get(conflict_type, {})

    def _phrases(side_key: str) -> str:
        side_tags = tag_map.get(side_key, [])
        found = [_TAG_PHRASES[t] for t in side_tags if t in pvt and t in _TAG_PHRASES]
        if not found:
            # Fallback: use any parallel_value_tags as a comma list
            found = pvt[:2] if pvt else ["great local options"]
        return " and ".join(found[:2])

    if conflict_type == "budget_vs_luxury":
        return template.format(
            name=name,
            budget_options=_phrases("budget"),
            luxury_options=_phrases("luxury"),
        )
    elif conflict_type == "adventure_vs_relaxation":
        return template.format(
            name=name,
            adventure_options=_phrases("adventure"),
            relax_options=_phrases("relax"),
        )
    elif conflict_type == "remote_vs_urban":
        return template.format(
            name=name,
            urban_options=_phrases("urban"),
            remote_options=_phrases("remote"),
        )
    else:
        return template.format(name=name)


# ── Top-Level Helper ───────────────────────────────────────────────────────────

def annotate_conflicts(
    conflicts: list[dict],
    top_destination: dict,
) -> list[dict]:
    """
    Attach a resolution_note to each detected conflict, resolved against the
    top-ranked destination.

    Returns the conflicts list with resolution_note added to each item.
    """
    annotated = []
    for c in conflicts:
        note = generate_resolution_note(c["type"], top_destination)
        annotated.append({**c, "resolution_note": note})
    return annotated
