"""
E.V. Assistant - Persistent Memory Module

Created: August 8, 2026
Last Edited: August 8, 2026
Author: Max Maehara

Purpose:
    Provides local persistent storage for E.V.'s conversation history
    and long-term memories.

How It Works:
    Uses a SQLite database stored at memory/memory.db.

    The database currently contains:
        - conversations: stores user prompts and E.V. responses
        - memories: stores long-term facts with categories

Most Recent Change:
    Added explicit long-term memory storage, retrieval, search,
    and deletion functions.
"""

import sqlite3
from pathlib import Path


# ---------------------------------------------------------------------------
# Paths / Configuration
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "memory" / "memory.db"

DB_PATH.parent.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# Database Connection
# ---------------------------------------------------------------------------

def get_connection():
    return sqlite3.connect(DB_PATH)


# ---------------------------------------------------------------------------
# Database Initialization
# ---------------------------------------------------------------------------

def init_memory():
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_message TEXT NOT NULL,
                ev_response TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                category TEXT DEFAULT 'general',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


# ---------------------------------------------------------------------------
# Conversation Memory
# ---------------------------------------------------------------------------

def save_conversation(user_message: str, ev_response: str):
    user_message = user_message.strip()
    ev_response = ev_response.strip()

    if not user_message or not ev_response:
        return

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO conversations (
                user_message,
                ev_response
            )
            VALUES (?, ?)
            """,
            (
                user_message,
                ev_response,
            ),
        )


def get_recent_conversations(limit: int = 5):
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                user_message,
                ev_response
            FROM conversations
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    rows.reverse()

    return rows


# ---------------------------------------------------------------------------
# Long-Term Memory
# ---------------------------------------------------------------------------

def save_memory(
    content: str,
    category: str = "general",
):
    content = content.strip()
    category = category.strip() or "general"

    if not content:
        return

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO memories (
                content,
                category
            )
            VALUES (?, ?)
            """,
            (
                content,
                category,
            ),
        )


def get_all_memories(limit: int = 100):
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT
                id,
                content,
                category,
                created_at
            FROM memories
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()


def search_memories(
    query: str,
    limit: int = 10,
):
    """
    Basic keyword search.

    This is intentionally simple for Memory V2.
    Later we can replace this with semantic/vector search.
    """

    query = query.strip()

    if not query:
        return []

    search_term = f"%{query}%"

    with get_connection() as conn:
        return conn.execute(
            """
            SELECT
                id,
                content,
                category,
                created_at
            FROM memories
            WHERE content LIKE ?
               OR category LIKE ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (
                search_term,
                search_term,
                limit,
            ),
        ).fetchall()


def delete_memory(memory_id: int):
    with get_connection() as conn:
        conn.execute(
            """
            DELETE FROM memories
            WHERE id = ?
            """,
            (memory_id,),
        )


# ---------------------------------------------------------------------------
# Debug / Standalone Test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    init_memory()

    print(f"E.V. memory database ready:")
    print(DB_PATH)

    print("\nRecent conversations:")

    for conversation in get_recent_conversations():
        print(conversation)

    print("\nLong-term memories:")

    for memory in get_all_memories():
        print(memory)