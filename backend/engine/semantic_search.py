"""
Semantic Search Engine
Converts destination descriptions + tags into vector embeddings using
sentence-transformers (free, runs entirely locally).

On first run the model (~90MB for all-MiniLM-L6-v2) is downloaded once
and cached by the HuggingFace hub. Subsequent startups are instant.

Public API
----------
precompute_embeddings(df)  — call once after data is loaded.
semantic_search(query, top_n) — rank destinations by meaning similarity.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Optional

_model = None
_embeddings: Optional[np.ndarray] = None
_dest_ids: list[str] = []
_dest_records: list[dict] = []


def _get_model():
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer("all-MiniLM-L6-v2")
            print("[SemanticSearch] Model loaded: all-MiniLM-L6-v2")
        except ImportError:
            print(
                "[SemanticSearch] sentence-transformers not installed. "
                "Semantic search will be disabled. Run: pip install sentence-transformers"
            )
            _model = None
    return _model


def precompute_embeddings(df: pd.DataFrame) -> None:
    """
    Pre-compute and cache embeddings for all destinations.
    Call this once during app startup after loading data.
    """
    global _embeddings, _dest_ids, _dest_records

    model = _get_model()
    if model is None:
        return

    # Build rich text per destination for embedding
    texts = []
    ids = []
    records = []
    for _, row in df.iterrows():
        combined = (
            f"{row.get('name', '')}. "
            f"{row.get('description', '')} "
            f"Tags: {row.get('tags', '')}. "
            f"Climate: {row.get('climate', '')}. "
            f"Best season: {row.get('best_season', '')}."
        )
        texts.append(combined)
        ids.append(str(row["id"]))
        records.append(row.to_dict())

    print(f"[SemanticSearch] Embedding {len(texts)} destinations…")
    _embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
    _dest_ids = ids
    _dest_records = records
    print("[SemanticSearch] Embeddings ready.")


def semantic_search(query: str, top_n: int = 10) -> list[dict]:
    """
    Find destinations whose conceptual meaning is closest to `query`.

    Returns a list of destination dicts enriched with a `semantic_score` field,
    sorted by descending similarity.
    """
    model = _get_model()
    if model is None or _embeddings is None or len(_dest_ids) == 0:
        return []

    query_vec = model.encode([query], convert_to_numpy=True)

    # Cosine similarity = dot product when vectors are L2-normalized
    norms = np.linalg.norm(_embeddings, axis=1, keepdims=True)
    normed = _embeddings / np.clip(norms, 1e-9, None)
    q_norm = query_vec / np.clip(np.linalg.norm(query_vec), 1e-9, None)

    scores = (normed @ q_norm.T).flatten()

    top_indices = np.argsort(scores)[::-1][:top_n]

    results = []
    for idx in top_indices:
        rec = dict(_dest_records[idx])
        rec["semantic_score"] = round(float(scores[idx]), 4)
        results.append(rec)

    return results
