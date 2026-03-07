"""
User View History — Short-Term Anti-Repetition Memory

Keeps an in-memory store of recently shown destination IDs per user.
Capped at `MAX_HISTORY` entries (circular/FIFO).

Public API
----------
record_seen(user_id, dest_ids)   — log destinations that were shown.
get_seen(user_id)                — retrieve the recent IDs list.
clear_seen(user_id)              — wipe a user's history.
all_history()                    — return full store (for debugging).
"""
from __future__ import annotations
from collections import deque

MAX_HISTORY = 20  # never remember more than this many per user

# { user_id: deque([dest_id, ...]) }
_history: dict[str, deque] = {}


def record_seen(user_id: str, dest_ids: list[str]) -> None:
    """Add destination IDs to the user's recent-seen list."""
    if user_id not in _history:
        _history[user_id] = deque(maxlen=MAX_HISTORY)
    for did in dest_ids:
        _history[user_id].append(str(did))


def get_seen(user_id: str) -> list[str]:
    """Return a list of recently seen destination IDs for this user."""
    if user_id not in _history:
        return []
    return list(_history[user_id])


def clear_seen(user_id: str) -> None:
    """Clear the view history for a user."""
    _history.pop(user_id, None)


def all_history() -> dict[str, list[str]]:
    """Return the full history store (all users). For debugging only."""
    return {uid: list(dq) for uid, dq in _history.items()}
