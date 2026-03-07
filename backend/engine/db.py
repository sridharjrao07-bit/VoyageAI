"""
SQLite Database Layer for Agentic History Tracking

Replaces the in-memory history logic to persist what destinations
a user has seen, preventing the "Same 8 Destinations" problem.
"""
import sqlite3
import os
from contextlib import contextmanager
from typing import List

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data.db")

@contextmanager
def get_db_connection():
    """Provide a transactional scope around a series of operations."""
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    """Initialize the SQLite database and create necessary tables if they don't exist."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rec_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                destination_id TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # Index for faster history lookups by user
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_rec_history_user_id 
            ON rec_history(user_id, timestamp DESC)
        ''')
        # Feedback Loop (RL) — stores liked destinations and their categories
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_likes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                destination_id TEXT NOT NULL,
                categories TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_user_likes_user_id
            ON user_likes(user_id, timestamp DESC)
        ''')
        # Community feedback table for Social Intelligence Agent
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                destination_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                comment_text TEXT NOT NULL,
                rating INTEGER DEFAULT 5,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_verified_visit BOOLEAN DEFAULT FALSE
            )
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_user_comments_dest_id
            ON user_comments(destination_id, timestamp DESC)
        ''')

def get_social_context(destination_id: str) -> str:
    """
    Fetch the 5 most recent comments to provide community feedback
    validation for the Social Intelligence Agent.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT comment_text, rating 
            FROM user_comments 
            WHERE destination_id = ? 
            ORDER BY timestamp DESC LIMIT 5
        """, (str(destination_id),))
        
        comments = cursor.fetchall()
        if not comments:
            return ""
        
        # Format them as a clean string for the LLM
        comment_string = " | ".join([f"({c[1]} stars) {c[0]}" for c in comments])
        return comment_string

def get_user_history(user_id: str, limit: int = 20) -> List[str]:
    """
    Fetch the last `limit` destinations seen by the user.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT destination_id 
            FROM rec_history 
            WHERE user_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (user_id, limit))
        return [row[0] for row in cursor.fetchall()]

def add_to_history(user_id: str, dest_ids: List[str]):
    """
    Record that a user has seen these specific destinations.
    """
    if not dest_ids:
        return
        
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Prepare batch insert
        records = [(user_id, str(d_id)) for d_id in dest_ids]
        cursor.executemany('''
            INSERT INTO rec_history (user_id, destination_id)
            VALUES (?, ?)
        ''', records)

def clear_user_history(user_id: str):
    """Clear history for a specific user (for testing or resets)."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM rec_history WHERE user_id = ?', (user_id,))


# ── Feedback Loop (RL) ─────────────────────────────────────────────────────

def save_like(user_id: str, destination_id: str, categories: List[str]) -> None:
    """
    Record that a user liked/saved a destination.
    `categories` is a list of tag strings for that destination.
    """
    cats_str = ','.join(categories)
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO user_likes (user_id, destination_id, categories) VALUES (?, ?, ?)',
            (user_id, str(destination_id), cats_str)
        )


def unlike(user_id: str, destination_id: str) -> None:
    """Remove a like (toggle off)."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'DELETE FROM user_likes WHERE user_id = ? AND destination_id = ?',
            (user_id, str(destination_id))
        )


def is_liked(user_id: str, destination_id: str) -> bool:
    """Check if a user has already liked a destination."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT 1 FROM user_likes WHERE user_id = ? AND destination_id = ? LIMIT 1',
            (user_id, str(destination_id))
        )
        return cursor.fetchone() is not None


def get_liked_categories(user_id: str, limit: int = 50) -> List[str]:
    """
    Return a frequency-sorted list of categories the user has liked.
    e.g. ['beach', 'beach', 'nature', 'hiking'] → useful for agent bias.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT categories FROM user_likes WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?',
            (user_id, limit)
        )
        rows = cursor.fetchall()

    all_cats: List[str] = []
    for (cats_str,) in rows:
        all_cats.extend([c.strip() for c in cats_str.split(',') if c.strip()])
    return all_cats


def get_liked_destination_ids(user_id: str) -> List[str]:
    """Return all destination IDs liked by the user."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT destination_id FROM user_likes WHERE user_id = ?',
            (user_id,)
        )
        return [row[0] for row in cursor.fetchall()]
