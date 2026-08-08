"""
E.V. Assistant - Persistent Memory Module

Created: August 8, 2026
Last Edited: August 8, 2026
Author: Max Maehara

Purpose:
    Provides local persistent storage for E.V.'s conversations and
    long-term memories.

How It Works:
    Uses a SQLite database stored at memory/memory.db.

    The database currently contains:
        - conversations: stores user prompts and E.V. responses
        - memories: stores long-term information with optional categories

    Memory is intentionally stored independently from the language model.
    This allows E.V.'s accumulated memory to remain available even when
    the underlying AI model is replaced in the future.

Most Recent Change:
    Created the initial SQLite database and conversation/memory table
    structure.
    Run file independently one time.
"""

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "memory" / "memory.db"

DB_PATH.parent.mkdir(exist_ok=True)


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_memory():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_message TEXT NOT NULL,
                ev_response TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                category TEXT DEFAULT 'general',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


def save_conversation(user_message: str, ev_response: str):
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO conversations (user_message, ev_response)
            VALUES (?, ?)
            """,
            (user_message, ev_response),
        )


def save_memory(content: str, category: str = "general"):
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO memories (content, category)
            VALUES (?, ?)
            """,
            (content, category),
        )


def get_recent_conversations(limit: int = 10):
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT user_message, ev_response
            FROM conversations
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    rows.reverse()
    return rows


def get_memories(limit: int = 20):
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT content, category
            FROM memories
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()


if __name__ == "__main__":
    init_memory()
    print(f"Memory initialized at: {DB_PATH}") 