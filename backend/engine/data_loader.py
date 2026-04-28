import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import MinMaxScaler

DATA_DIR = Path(__file__).parent.parent / "data"

_destinations_df = None
_users_df = None
_ratings_df = None
_tfidf_matrix = None
_tfidf_vectorizer = None
_dest_id_to_idx = {}
_idx_to_dest_id = {}
_last_sanitization_report: dict = {}


def load_data():
    global _destinations_df, _users_df, _ratings_df
    global _tfidf_matrix, _tfidf_vectorizer
    global _dest_id_to_idx, _idx_to_dest_id
    global _last_sanitization_report

    # Load raw CSVs
    raw_destinations = pd.read_csv(DATA_DIR / "destinations.csv")
    raw_destinations["id"] = raw_destinations["id"].astype(str)

    raw_ratings = pd.read_csv(DATA_DIR / "ratings.csv")
    raw_ratings["user_id"] = raw_ratings["user_id"].astype(str)
    raw_ratings["destination_id"] = raw_ratings["destination_id"].astype(str)

    # ── Sanitize before anything else touches the data ──────────────────────
    from engine.sanitizer import sanitize_dataframes
    _destinations_df, _ratings_df, _last_sanitization_report = sanitize_dataframes(
        raw_destinations, raw_ratings, max_age_days=30, strict_geo=False
    )
    print(f"[Sanitizer] Report: {_last_sanitization_report}")

    # Build TF-IDF on tags + description
    _destinations_df["content"] = (
        _destinations_df["tags"].fillna("") + " " +
        _destinations_df["description"].fillna("") + " " +
        _destinations_df["climate"].fillna("") + " " +
        _destinations_df["best_season"].fillna("")
    )

    _tfidf_vectorizer = TfidfVectorizer(stop_words="english", max_features=300)
    _tfidf_matrix = _tfidf_vectorizer.fit_transform(_destinations_df["content"])

    # ID index maps
    for i, dest_id in enumerate(_destinations_df["id"].values):
        _dest_id_to_idx[dest_id] = i
        _idx_to_dest_id[i] = dest_id

    # Load users
    _users_df = pd.read_csv(DATA_DIR / "users.csv")
    _users_df["user_id"] = _users_df["user_id"].astype(str)

    print(f"[DataLoader] Loaded {len(_destinations_df)} destinations, "
          f"{len(_users_df)} users, {len(_ratings_df)} ratings.")


def get_destinations():
    return _destinations_df


def get_users():
    return _users_df


def get_ratings():
    return _ratings_df


def get_tfidf_matrix():
    return _tfidf_matrix


def get_tfidf_vectorizer():
    return _tfidf_vectorizer


def get_dest_index_maps():
    return _dest_id_to_idx, _idx_to_dest_id


def get_user_by_id(user_id: str):
    if _users_df is None:
        return None
    match = _users_df[_users_df["user_id"] == user_id]
    return match.iloc[0] if not match.empty else None


def get_sanitization_report() -> dict:
    """Return the sanitization report from the last load_data() call."""
    return _last_sanitization_report
