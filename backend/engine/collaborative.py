"""
Collaborative Filtering
User-based CF using cosine similarity on the rating matrix.
Falls back to popularity baseline for cold-start users.

Ghost-User Filter: ratings from users with no activity in the last 30 days
are excluded before building the similarity matrix, preventing stale/fake
profiles from polluting collaborative scores.
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone
from sklearn.metrics.pairwise import cosine_similarity
from engine.data_loader import get_ratings, get_destinations

GHOST_USER_DAYS = 30   # users inactive longer than this are "ghosts"


def _filter_ghost_users(ratings: pd.DataFrame) -> pd.DataFrame:
    """
    Remove ratings made by ghost users — users whose MOST RECENT rating
    is older than GHOST_USER_DAYS. This keeps the collaborative signal fresh.
    """
    if "timestamp" not in ratings.columns:
        return ratings   # no timestamp column, skip filter

    ratings = ratings.copy()
    ratings["_ts"] = pd.to_datetime(ratings["timestamp"], errors="coerce", utc=True)
    cutoff = datetime.now(timezone.utc) - timedelta(days=GHOST_USER_DAYS)

    # Last activity per user
    last_active = ratings.groupby("user_id")["_ts"].max()
    active_users = last_active[last_active >= cutoff].index
    filtered = ratings[ratings["user_id"].isin(active_users)].drop(columns=["_ts"])

    ghost_count = ratings["user_id"].nunique() - len(active_users)
    if ghost_count > 0:
        print(f"[Collaborative] Ghost-user filter removed {ghost_count} inactive user(s).")
    return filtered


def _build_rating_matrix():
    ratings = get_ratings()
    if ratings is None or ratings.empty:
        return None, None, None

    # Filter ghost users before building the matrix
    ratings = _filter_ghost_users(ratings)
    if ratings.empty:
        return None, None, None

    matrix = ratings.pivot_table(
        index="user_id",
        columns="destination_id",
        values="rating",
        fill_value=0,
    )
    return matrix, matrix.index.tolist(), matrix.columns.tolist()



def score_by_collaborative(user_id: str, top_n: int = 50) -> dict[str, float]:
    """
    Returns a dict { destination_id: predicted_rating_score }.
    For cold-start (unknown) users returns an empty dict.
    """
    matrix, user_ids, dest_ids = _build_rating_matrix()
    if matrix is None or user_id not in user_ids:
        return {}  # cold-start fallback handled by hybrid

    user_idx = user_ids.index(user_id)
    user_vec = matrix.values[user_idx].reshape(1, -1)

    sim_scores = cosine_similarity(user_vec, matrix.values).flatten()

    # Weighted sum of other users' ratings
    sim_scores[user_idx] = 0  # exclude self
    weights = np.maximum(sim_scores, 0)
    weight_sum = weights.sum()

    if weight_sum == 0:
        return {}

    predicted = weights @ matrix.values / (weight_sum + 1e-9)

    scores = {}
    already_rated = set(
        matrix.columns[(matrix.values[user_idx] > 0)].tolist()
    )
    for i, dest_id in enumerate(dest_ids):
        if dest_id not in already_rated:
            scores[dest_id] = float(predicted[i])

    return scores


def get_popularity_scores() -> dict[str, float]:
    """
    Popularity baseline: average rating × log(count+1).
    """
    ratings = get_ratings()
    if ratings is None or ratings.empty:
        return {}

    agg = ratings.groupby("destination_id")["rating"].agg(["mean", "count"])
    agg["popularity"] = agg["mean"] * np.log1p(agg["count"])
    # Normalize 0-1
    max_pop = agg["popularity"].max()
    if max_pop > 0:
        agg["popularity"] /= max_pop
    return agg["popularity"].to_dict()
