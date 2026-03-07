"""
Content-Based Filtering
Uses TF-IDF cosine similarity to score destinations
against the user's explicit tag/preference query.
"""
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from engine.data_loader import (
    get_tfidf_matrix,
    get_tfidf_vectorizer,
    get_destinations,
    get_dest_index_maps,
)


def score_by_content(query_tags: list[str], top_n: int = 50) -> dict[str, float]:
    """
    Returns a dict { destination_id: cosine_similarity_score }
    for the top_n destinations most similar to the user's tags.
    """
    vectorizer = get_tfidf_vectorizer()
    tfidf_matrix = get_tfidf_matrix()
    destinations = get_destinations()
    dest_id_to_idx, idx_to_dest_id = get_dest_index_maps()

    if vectorizer is None or tfidf_matrix is None:
        return {}

    query = " ".join(query_tags)
    query_vec = vectorizer.transform([query])

    cosine_scores = cosine_similarity(query_vec, tfidf_matrix).flatten()

    # Build id -> score dict
    scores = {}
    for idx, score in enumerate(cosine_scores):
        dest_id = idx_to_dest_id.get(idx)
        if dest_id is not None:
            scores[dest_id] = float(score)

    return scores
