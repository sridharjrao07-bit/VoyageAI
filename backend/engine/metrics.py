"""
Performance Metrics
Computes Precision@K, Recall@K, MAP and A/B test comparison.
"""
import numpy as np
import pandas as pd
from engine.data_loader import get_ratings, get_destinations
from engine.collaborative import get_popularity_scores


def _get_relevant_items(user_id: str, threshold: float = 4.0) -> set:
    ratings = get_ratings()
    if ratings is None:
        return set()
    user_ratings = ratings[
        (ratings["user_id"] == user_id) & (ratings["rating"] >= threshold)
    ]
    return set(user_ratings["destination_id"].tolist())


def precision_at_k(recommended: list, relevant: set, k: int) -> float:
    top_k = recommended[:k]
    hits = sum(1 for r in top_k if r in relevant)
    return hits / k if k > 0 else 0.0


def recall_at_k(recommended: list, relevant: set, k: int) -> float:
    top_k = recommended[:k]
    hits = sum(1 for r in top_k if r in relevant)
    return hits / len(relevant) if relevant else 0.0


def average_precision(recommended: list, relevant: set) -> float:
    if not relevant:
        return 0.0
    hits, score = 0, 0.0
    for i, r in enumerate(recommended):
        if r in relevant:
            hits += 1
            score += hits / (i + 1)
    return score / len(relevant)


def mean_average_precision(users_recs: dict, users_relevant: dict) -> float:
    aps = [
        average_precision(users_recs.get(uid, []), users_relevant.get(uid, set()))
        for uid in users_relevant
    ]
    return float(np.mean(aps)) if aps else 0.0


def compute_full_metrics() -> dict:
    """
    Simulate evaluation over known users using leave-one-out strategy.
    """
    from engine.hybrid import recommend as hybrid_recommend

    ratings = get_ratings()
    if ratings is None or ratings.empty:
        return {}

    # Sample up to 20 users that have >= 5 ratings
    user_counts = ratings.groupby("user_id").size()
    eligible = user_counts[user_counts >= 5].index.tolist()
    sample_users = eligible[:20]

    K = 10
    precision_scores, recall_scores, ap_scores = [], [], []
    ab_hybrid, ab_popular = [], []

    popular_scores = get_popularity_scores()
    popular_ranked = sorted(popular_scores, key=lambda x: -popular_scores[x])

    for uid in sample_users:
        relevant = _get_relevant_items(uid, threshold=4.0)
        if not relevant:
            continue

        # Hybrid recommendations
        recs = hybrid_recommend(uid, tags=[], budget_usd=0, accessibility_required=False, top_n=K)
        rec_ids = [r["id"] for r in recs]

        p = precision_at_k(rec_ids, relevant, K)
        r = recall_at_k(rec_ids, relevant, K)
        ap = average_precision(rec_ids, relevant)

        precision_scores.append(p)
        recall_scores.append(r)
        ap_scores.append(ap)

        # A/B baseline (popularity)
        pop_p = precision_at_k(popular_ranked, relevant, K)
        ab_hybrid.append(p)
        ab_popular.append(pop_p)

    return {
        "precision_at_10": round(float(np.mean(precision_scores)), 4) if precision_scores else 0,
        "recall_at_10": round(float(np.mean(recall_scores)), 4) if recall_scores else 0,
        "map_score": round(float(np.mean(ap_scores)), 4) if ap_scores else 0,
        "ab_test": {
            "hybrid_precision": round(float(np.mean(ab_hybrid)), 4) if ab_hybrid else 0,
            "popularity_precision": round(float(np.mean(ab_popular)), 4) if ab_popular else 0,
            "improvement_pct": round(
                ((np.mean(ab_hybrid) - np.mean(ab_popular)) / (np.mean(ab_popular) + 1e-9)) * 100, 2
            ) if ab_popular else 0,
        },
        "users_evaluated": len(precision_scores),
        "k": K,
    }
