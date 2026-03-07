"""
Data Sanitization Module
Validates and cleans destination and ratings DataFrames before they reach the AI engine.

Checks:
  1. Placeholder strings  — removes rows with fake/test names or descriptions.
  2. Age filter           — drops ratings older than 30 days.
  3. Geo bounding box     — ensures lat/lon are physically valid world coordinates.
                           Optionally applies a tighter regional bounding box for
                           South / Southeast / East Asia trekking destinations.

Usage:
    from engine.sanitizer import sanitize_dataframes
    dest_df, ratings_df, report = sanitize_dataframes(dest_df, ratings_df)
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Optional

import pandas as pd

# ── Placeholder detection ────────────────────────────────────────────────────
_PLACEHOLDER_PATTERNS: list[str] = [
    r"\btest\b",
    r"\bN/A\b",
    r"\bNA\b",
    r"\bnull\b",
    r"\bundefined\b",
    r"\bplaceholder\b",
    r"\bfake\b",
    r"\bsample\b",
    r"\bdummy\b",
    r"\bexample\b",
    r"\btbd\b",
    r"\bfoo\b",
    r"\bbar\b",
    r"^\d{1,6}$",          # pure numeric strings like "123"
    r"^[_\-\s]+$",         # blank / whitespace-only
]
_PLACEHOLDER_REGEX = re.compile(
    "|".join(_PLACEHOLDER_PATTERNS), re.IGNORECASE
)


def _is_placeholder(value: str) -> bool:
    """Return True if the string looks like fake / test data."""
    if not isinstance(value, str) or not value.strip():
        return True
    return bool(_PLACEHOLDER_REGEX.search(value.strip()))


# ── World bounding box ───────────────────────────────────────────────────────
WORLD_LAT_MIN, WORLD_LAT_MAX = -90.0, 90.0
WORLD_LON_MIN, WORLD_LON_MAX = -180.0, 180.0

# Optional tighter box: South/Southeast/East Asia + Himalayan trekking belt
ASIA_TREK_BOX = {
    "lat_min": -10.0,
    "lat_max": 55.0,
    "lon_min": 60.0,
    "lon_max": 150.0,
}

# Coordinates that are obviously wrong (ocean nulls, default zeros)
_GHOST_COORDINATE_PAIRS = [(0.0, 0.0), (0.0, 1.0), (1.0, 0.0)]
_GHOST_COORD_TOLERANCE = 0.01   # within 0.01 degree of a ghost pair = suspicious


def _valid_coords(lat: float, lon: float, strict_asia: bool = False) -> bool:
    """Return True if coordinates fall within the allowed bounding box."""
    if not (WORLD_LAT_MIN <= lat <= WORLD_LAT_MAX):
        return False
    if not (WORLD_LON_MIN <= lon <= WORLD_LON_MAX):
        return False

    # Zero-Trust: reject (0,0) and other ghost null-island coordinates
    for ghost_lat, ghost_lon in _GHOST_COORDINATE_PAIRS:
        if (abs(lat - ghost_lat) < _GHOST_COORD_TOLERANCE and
                abs(lon - ghost_lon) < _GHOST_COORD_TOLERANCE):
            return False

    if strict_asia:
        box = ASIA_TREK_BOX
        return (box["lat_min"] <= lat <= box["lat_max"] and
                box["lon_min"] <= lon <= box["lon_max"])
    return True



# ── Main sanitizer ───────────────────────────────────────────────────────────

def sanitize_dataframes(
    destinations: pd.DataFrame,
    ratings: Optional[pd.DataFrame] = None,
    max_age_days: int = 30,
    strict_geo: bool = False,
) -> tuple[pd.DataFrame, Optional[pd.DataFrame], dict]:
    """
    Sanitize destination and ratings DataFrames.

    Parameters
    ----------
    destinations  : Raw destinations DataFrame.
    ratings       : Raw ratings DataFrame (may be None).
    max_age_days  : Ratings older than this are dropped (default 30 days).
    strict_geo    : If True, apply the Asian trekking bounding box.

    Returns
    -------
    clean_dest    : Sanitized destinations DataFrame.
    clean_ratings : Sanitized ratings DataFrame (or None).
    report        : Summary dict of what was removed and why.
    """
    report: dict = {
        "total_destinations_before": len(destinations),
        "removed_placeholder_destinations": 0,
        "removed_invalid_coords": 0,
        "total_destinations_after": 0,
        "total_ratings_before": len(ratings) if ratings is not None else 0,
        "removed_stale_ratings": 0,
        "total_ratings_after": 0,
        "flagged_destination_names": [],
    }

    # ── 1. Placeholder check on destinations ────────────────────────────────
    placeholder_mask = (
        destinations["name"].apply(_is_placeholder) |
        destinations["country"].apply(_is_placeholder) |
        destinations["description"].apply(_is_placeholder)
    )
    flagged = destinations.loc[placeholder_mask, "name"].tolist()
    report["removed_placeholder_destinations"] = int(placeholder_mask.sum())
    report["flagged_destination_names"] = flagged
    destinations = destinations[~placeholder_mask].copy()

    # ── 2. Geo bounding box ─────────────────────────────────────────────────
    def _coord_ok(row) -> bool:
        try:
            return _valid_coords(
                float(row["latitude"]),
                float(row["longitude"]),
                strict_asia=strict_geo,
            )
        except (ValueError, TypeError):
            return False

    geo_mask = destinations.apply(_coord_ok, axis=1)
    bad_geo = (~geo_mask).sum()
    report["removed_invalid_coords"] = int(bad_geo)
    destinations = destinations[geo_mask].copy()

    report["total_destinations_after"] = len(destinations)

    # ── 3. Age filter on ratings ─────────────────────────────────────────────
    clean_ratings = ratings
    if ratings is not None and not ratings.empty:
        cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)

        if "timestamp" in ratings.columns:
            ratings["_ts"] = pd.to_datetime(
                ratings["timestamp"], errors="coerce", utc=True
            )
            stale_mask = ratings["_ts"] < cutoff
            report["removed_stale_ratings"] = int(stale_mask.sum())
            clean_ratings = ratings[~stale_mask].drop(columns=["_ts"]).copy()
        else:
            # No timestamp column — nothing to age-filter
            clean_ratings = ratings.copy()

        report["total_ratings_after"] = len(clean_ratings)
    else:
        report["total_ratings_after"] = 0

    return destinations, clean_ratings, report
