"""
Async PostgreSQL Database Layer for Agentic History Tracking

Replaces the synchronous SQLite implementation with async PostgreSQL
operations using SQLAlchemy 2.0 + asyncpg.

All public functions maintain the same signatures as the original
SQLite version so callers (main.py) can switch with minimal changes.
"""
from __future__ import annotations

from typing import List

from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from database import async_session
from models import RecHistory, UserLike, UserComment


# ---------------------------------------------------------------------------
# Init
# ---------------------------------------------------------------------------

async def init_db() -> None:
    """
    Initialize the database — creates tables and the pgvector extension.
    Called once at application startup via the FastAPI lifespan.
    """
    from database import init_models
    await init_models()
    print("[DB] PostgreSQL tables initialised (pgvector enabled).")


# ---------------------------------------------------------------------------
# Social Intelligence
# ---------------------------------------------------------------------------

async def get_social_context(destination_id: str) -> str:
    """
    Fetch the 5 most recent comments for the Social Intelligence Agent.
    """
    async with async_session() as session:
        stmt = (
            select(UserComment.comment_text, UserComment.rating)
            .where(UserComment.destination_id == str(destination_id))
            .order_by(UserComment.timestamp.desc())
            .limit(5)
        )
        result = await session.execute(stmt)
        comments = result.all()

    if not comments:
        return ""
    return " | ".join(f"({c.rating} stars) {c.comment_text}" for c in comments)


# ---------------------------------------------------------------------------
# Recommendation History
# ---------------------------------------------------------------------------

async def get_user_history(user_id: str, limit: int = 20) -> List[str]:
    """Fetch the last `limit` destinations seen by the user."""
    async with async_session() as session:
        stmt = (
            select(RecHistory.destination_id)
            .where(RecHistory.user_id == user_id)
            .order_by(RecHistory.timestamp.desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        return [row[0] for row in result.all()]


async def add_to_history(user_id: str, dest_ids: List[str]) -> None:
    """Record that a user has seen these destinations."""
    if not dest_ids:
        return
    async with async_session() as session:
        for d_id in dest_ids:
            session.add(RecHistory(user_id=user_id, destination_id=str(d_id)))
        await session.commit()


async def clear_user_history(user_id: str) -> None:
    """Clear history for a specific user."""
    async with async_session() as session:
        await session.execute(
            delete(RecHistory).where(RecHistory.user_id == user_id)
        )
        await session.commit()


# ---------------------------------------------------------------------------
# Feedback Loop (RL) — Likes / Bucket List
# ---------------------------------------------------------------------------

async def save_like(user_id: str, destination_id: str, categories: List[str]) -> None:
    """Record that a user liked/saved a destination."""
    cats_str = ",".join(categories)
    async with async_session() as session:
        session.add(
            UserLike(
                user_id=user_id,
                destination_id=str(destination_id),
                categories=cats_str,
            )
        )
        await session.commit()


async def unlike(user_id: str, destination_id: str) -> None:
    """Remove a like (toggle off)."""
    async with async_session() as session:
        await session.execute(
            delete(UserLike).where(
                UserLike.user_id == user_id,
                UserLike.destination_id == str(destination_id),
            )
        )
        await session.commit()


async def is_liked(user_id: str, destination_id: str) -> bool:
    """Check if a user has already liked a destination."""
    async with async_session() as session:
        stmt = (
            select(UserLike.id)
            .where(
                UserLike.user_id == user_id,
                UserLike.destination_id == str(destination_id),
            )
            .limit(1)
        )
        result = await session.execute(stmt)
        return result.first() is not None


async def get_liked_categories(user_id: str, limit: int = 50) -> List[str]:
    """
    Return a frequency-sorted list of categories the user has liked.
    Useful for agent RL bias.
    """
    async with async_session() as session:
        stmt = (
            select(UserLike.categories)
            .where(UserLike.user_id == user_id)
            .order_by(UserLike.timestamp.desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        rows = result.all()

    all_cats: List[str] = []
    for (cats_str,) in rows:
        all_cats.extend([c.strip() for c in cats_str.split(",") if c.strip()])
    return all_cats


async def get_liked_destination_ids(user_id: str) -> List[str]:
    """Return all destination IDs liked by the user."""
    async with async_session() as session:
        stmt = select(UserLike.destination_id).where(UserLike.user_id == user_id)
        result = await session.execute(stmt)
        return [row[0] for row in result.all()]
