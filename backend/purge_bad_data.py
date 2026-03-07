"""
Smart Tourism — CSV Data Sanitization Script
Equivalent to the SQLite purge script, adapted for the CSV-based data layer.

Run this standalone to:
  1. Remove destinations with fake/placeholder/test names
  2. Remove ratings from ghost users (inactive > 30 days)
  3. Save cleaned CSVs back to the data/ directory

Usage:
    python purge_bad_data.py              # dry run (preview only)
    python purge_bad_data.py --commit     # actually overwrite CSV files
"""
import sys
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).parent / "data"
DRY_RUN  = "--commit" not in sys.argv

# ── Bad keyword patterns (same logic as engine/sanitizer.py) ─────────────────
BAD_PATTERNS = re.compile(
    r"\btest\b|\bplaceholder\b|\bn/a\b|\bna\b|\bnull\b|\bundefined\b"
    r"|\bfake\b|\bsample\b|\bdummy\b|\bexample\b|\btbd\b|^\d{1,6}$",
    re.IGNORECASE
)

GHOST_USER_DAYS = 30   # users inactive longer than this are purged


def is_bad(value: str) -> bool:
    return not isinstance(value, str) or bool(BAD_PATTERNS.search(str(value).strip()))


def is_zero_island(lat: float, lon: float, tol: float = 0.01) -> bool:
    """Reject (0,0) ghost coordinates — the Null Island problem."""
    ghost_pairs = [(0.0, 0.0), (0.0, 1.0), (1.0, 0.0)]
    return any(abs(lat - g_lat) < tol and abs(lon - g_lon) < tol
               for g_lat, g_lon in ghost_pairs)


print("=" * 60)
print(f"Smart Tourism — Data Purge Script  (dry_run={DRY_RUN})")
print("=" * 60)

# ── 1. Load ──────────────────────────────────────────────────────
destinations = pd.read_csv(DATA_DIR / "destinations.csv")
users        = pd.read_csv(DATA_DIR / "users.csv")
ratings      = pd.read_csv(DATA_DIR / "ratings.csv")

print(f"\nBefore purge:")
print(f"  Destinations : {len(destinations)}")
print(f"  Users        : {len(users)}")
print(f"  Ratings      : {len(ratings)}")

# ── 2. Purge fake/placeholder destinations ───────────────────────
bad_dest_mask = (
    destinations["name"].apply(is_bad) |
    destinations["description"].apply(is_bad) |
    destinations["country"].apply(is_bad)
)
flagged_names = destinations.loc[bad_dest_mask, "name"].tolist()

# Also purge ghost coordinates (0,0)
zero_mask = destinations.apply(
    lambda r: is_zero_island(float(r["latitude"]), float(r["longitude"])), axis=1
)
bad_dest_mask = bad_dest_mask | zero_mask

n_dest_removed = int(bad_dest_mask.sum())
clean_destinations = destinations[~bad_dest_mask].copy()

print(f"\n[Destinations]")
print(f"  Fake/test/placeholder  : {n_dest_removed}")
print(f"  Ghost coords (0,0)    : {int(zero_mask.sum())}")
if flagged_names:
    print(f"  Flagged names         : {flagged_names}")
else:
    print(f"  No bad names found — data is clean.")

# ── 3. Purge ghost users (inactive > 30 days) ────────────────────
cutoff = datetime.now(timezone.utc) - timedelta(days=GHOST_USER_DAYS)
n_ghost_users = 0

if "last_login" in users.columns:
    users["_ts"] = pd.to_datetime(users["last_login"], errors="coerce", utc=True)
    ghost_mask   = users["_ts"] < cutoff
    n_ghost_users = int(ghost_mask.sum())
    ghost_ids    = users.loc[ghost_mask, "user_id"].tolist()
    clean_users  = users[~ghost_mask].drop(columns=["_ts"]).copy()
    print(f"\n[Users]")
    print(f"  Ghost users removed (>30d inactive): {n_ghost_users}")
    if ghost_ids:
        print(f"  Ghost user IDs: {ghost_ids[:10]}")
else:
    clean_users = users.copy()
    ghost_ids   = []
    print(f"\n[Users]")
    print(f"  No 'last_login' column — skipping ghost-user purge.")

# ── 4. Purge stale ratings (>30 days old OR from ghost users) ────
n_ratings_removed = 0
clean_ratings = ratings.copy()

if "timestamp" in ratings.columns:
    ratings["_ts"] = pd.to_datetime(ratings["timestamp"], errors="coerce", utc=True)
    stale_mask      = ratings["_ts"] < cutoff
    ghost_r_mask    = ratings["user_id"].isin(ghost_ids) if ghost_ids else pd.Series(False, index=ratings.index)
    remove_mask     = stale_mask | ghost_r_mask
    n_ratings_removed = int(remove_mask.sum())
    clean_ratings = ratings[~remove_mask].drop(columns=["_ts"]).copy()
else:
    print(f"\n[Ratings]")
    print(f"  No 'timestamp' column — skipping stale-rating purge.")

print(f"\n[Ratings]  Stale/ghost ratings removed: {n_ratings_removed}")

# ── 5. Summary ───────────────────────────────────────────────────
print(f"\nAfter purge:")
print(f"  Destinations : {len(clean_destinations)}")
print(f"  Users        : {len(clean_users)}")
print(f"  Ratings      : {len(clean_ratings)}")
print(f"\n  Total records purged: {n_dest_removed + n_ghost_users + n_ratings_removed}")

# ── 6. Save (only if --commit flag is passed) ────────────────────
if not DRY_RUN:
    print(f"\n[DRY RUN] No files written. Re-run with --commit to apply.")
else:
    clean_destinations.to_csv(DATA_DIR / "destinations.csv", index=False)
    clean_users.to_csv(DATA_DIR / "users.csv", index=False)
    clean_ratings.to_csv(DATA_DIR / "ratings.csv", index=False)
    print(f"\n[COMMITTED] Cleaned CSVs written to {DATA_DIR.resolve()}")

print("=" * 60)
print("Purge complete.")
