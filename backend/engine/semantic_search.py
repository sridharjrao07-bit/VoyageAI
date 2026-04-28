"""
Semantic Search Engine — pgvector implementation

Uses PostgreSQL pgvector extension for cosine similarity search
instead of in-memory numpy computation.

Public API (unchanged for callers):
  precompute_embeddings(df)  — Upserts destination rows + embeddings into Postgres.
  semantic_search(query, top_n) — Cosine similarity search via pgvector <=> operator.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Optional

from sqlalchemy import select, text
from pgvector.sqlalchemy import Vector

_model = None


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


async def precompute_embeddings(df: pd.DataFrame) -> None:
    """
    Pre-compute embeddings for all destinations and upsert them
    into the PostgreSQL `destinations` table (with pgvector column).
    """
    model = _get_model()
    if model is None:
        return

    from database import async_session
    from models import Destination

    texts = []
    rows_data = []
    for _, row in df.iterrows():
        combined = (
            f"{row.get('name', '')}. "
            f"{row.get('description', '')} "
            f"Tags: {row.get('tags', '')}. "
            f"Climate: {row.get('climate', '')}. "
            f"Best season: {row.get('best_season', '')}."
        )
        texts.append(combined)
        rows_data.append(row.to_dict())

    print(f"[SemanticSearch] Embedding {len(texts)} destinations…")
    embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)

    async with async_session() as session:
        for i, row_dict in enumerate(rows_data):
            dest_id = str(row_dict["id"])
            embedding_list = embeddings[i].tolist()

            # Check if destination already exists
            existing = await session.get(Destination, dest_id)
            if existing:
                existing.embedding = embedding_list
                # Update other fields too in case CSV data changed
                existing.name = str(row_dict.get("name", ""))
                existing.country = str(row_dict.get("country", ""))
                existing.continent = str(row_dict.get("continent", ""))
                existing.description = str(row_dict.get("description", ""))
                existing.tags = str(row_dict.get("tags", ""))
                existing.climate = str(row_dict.get("climate", ""))
                existing.best_season = str(row_dict.get("best_season", ""))
                existing.avg_cost_usd = float(row_dict.get("avg_cost_usd", 0))
                existing.latitude = float(row_dict.get("latitude", 0))
                existing.longitude = float(row_dict.get("longitude", 0))
                existing.accessibility = str(row_dict.get("accessibility", "false"))
                existing.popularity = float(row_dict.get("popularity", 0))
            else:
                dest = Destination(
                    id=dest_id,
                    name=str(row_dict.get("name", "")),
                    country=str(row_dict.get("country", "")),
                    continent=str(row_dict.get("continent", "")),
                    description=str(row_dict.get("description", "")),
                    tags=str(row_dict.get("tags", "")),
                    climate=str(row_dict.get("climate", "")),
                    best_season=str(row_dict.get("best_season", "")),
                    avg_cost_usd=float(row_dict.get("avg_cost_usd", 0)),
                    latitude=float(row_dict.get("latitude", 0)),
                    longitude=float(row_dict.get("longitude", 0)),
                    accessibility=str(row_dict.get("accessibility", "false")),
                    popularity=float(row_dict.get("popularity", 0)),
                    embedding=embedding_list,
                )
                session.add(dest)

        await session.commit()

    print("[SemanticSearch] Embeddings stored in PostgreSQL (pgvector).")


async def semantic_search(query: str, top_n: int = 10) -> list[dict]:
    """
    Find destinations whose conceptual meaning is closest to `query`
    using pgvector cosine distance operator (<=>).

    Returns a list of destination dicts enriched with a `semantic_score` field,
    sorted by ascending cosine distance (= descending similarity).
    """
    model = _get_model()
    if model is None:
        return []

    from database import async_session
    from models import Destination

    query_vec = model.encode([query], convert_to_numpy=True)
    query_list = query_vec[0].tolist()

    async with async_session() as session:
        # pgvector cosine distance: column <=> query_vector
        # Lower distance = higher similarity
        stmt = (
            select(
                Destination,
                Destination.embedding.cosine_distance(query_list).label("distance"),
            )
            .where(Destination.embedding.isnot(None))
            .order_by("distance")
            .limit(top_n)
        )
        result = await session.execute(stmt)
        rows = result.all()

    results = []
    for dest, distance in rows:
        rec = {
            "id": dest.id,
            "name": dest.name,
            "country": dest.country,
            "continent": dest.continent,
            "description": dest.description,
            "tags": dest.tags,
            "climate": dest.climate,
            "best_season": dest.best_season,
            "avg_cost_usd": dest.avg_cost_usd,
            "latitude": dest.latitude,
            "longitude": dest.longitude,
            "accessibility": dest.accessibility,
            "popularity": dest.popularity,
            # cosine_distance = 1 - cosine_similarity, so similarity = 1 - distance
            "semantic_score": round(1.0 - float(distance), 4),
        }
        results.append(rec)

    return results
