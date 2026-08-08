"""
E.V.I.E. - Memory Database Module

Created: August 8, 2026
Last Edited: August 8, 2026
Author: Max Maehara

Purpose:
    Owns E.V.I.E.'s persistent SQLite memory database.

How It Works:
    Stores conversation history, active long-term memories,
    semantic embeddings, metadata, archived memories, and
    supersession relationships.

    This module performs storage operations only. It does not
    decide what should be remembered.

Most Recent Change:
    Added soft deletion, supersession tracking, compact debugging,
    embedding storage, restoration, and multi-memory operations.
"""

import sqlite3
from pathlib import Path


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = ROOT / "memory" / "memory.db"

DB_PATH.parent.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------------

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------------------------------------------------------------------
# Initialization / Migration
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

    migrate_memory_schema()


def migrate_memory_schema():
    additions = {
        "importance": "INTEGER DEFAULT 50",
        "permanence": "INTEGER DEFAULT 50",
        "confidence": "INTEGER DEFAULT 100",
        "source": "TEXT DEFAULT 'manual'",
        "updated_at": "TIMESTAMP",
        "embedding": "TEXT",
        "active": "INTEGER DEFAULT 1",
        "deleted_at": "TIMESTAMP",
        "superseded_by": "INTEGER",
        "archive_reason": "TEXT",
    }

    with get_connection() as conn:
        existing_columns = {
            row["name"]
            for row in conn.execute(
                "PRAGMA table_info(memories)"
            ).fetchall()
        }

        for column_name, definition in additions.items():
            if column_name not in existing_columns:
                conn.execute(
                    f"""
                    ALTER TABLE memories
                    ADD COLUMN {column_name} {definition}
                    """
                )


# ---------------------------------------------------------------------------
# Conversation History
# ---------------------------------------------------------------------------

def save_conversation(
    user_message: str,
    ev_response: str,
):
    user_message = user_message.strip()
    ev_response = ev_response.strip()

    if not user_message or not ev_response:
        return None

    with get_connection() as conn:
        cursor = conn.execute(
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

        return cursor.lastrowid


def get_recent_conversations(
    limit: int = 5,
):
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

    rows = list(reversed(rows))

    return [
        (
            row["user_message"],
            row["ev_response"],
        )
        for row in rows
    ]


# ---------------------------------------------------------------------------
# Save Long-Term Memory
# ---------------------------------------------------------------------------

def save_memory(
    content: str,
    category: str = "general",
    importance: int = 50,
    permanence: int = 50,
    confidence: int = 100,
    source: str = "manual",
    embedding: str | None = None,
):
    content = content.strip()
    category = category.strip().lower() or "general"
    source = source.strip().lower() or "manual"

    if not content:
        return None

    importance = max(0, min(100, int(importance)))
    permanence = max(0, min(100, int(permanence)))
    confidence = max(0, min(100, int(confidence)))

    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO memories (
                content,
                category,
                importance,
                permanence,
                confidence,
                source,
                embedding,
                active,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
            """,
            (
                content,
                category,
                importance,
                permanence,
                confidence,
                source,
                embedding,
            ),
        )

        return cursor.lastrowid


# ---------------------------------------------------------------------------
# Retrieve Memories
# ---------------------------------------------------------------------------

def get_memory(
    memory_id: int,
    include_inactive: bool = False,
):
    with get_connection() as conn:
        if include_inactive:
            row = conn.execute(
                """
                SELECT *
                FROM memories
                WHERE id = ?
                """,
                (memory_id,),
            ).fetchone()
        else:
            row = conn.execute(
                """
                SELECT *
                FROM memories
                WHERE id = ?
                  AND active = 1
                """,
                (memory_id,),
            ).fetchone()

    return dict(row) if row else None


def get_memories_by_ids(
    memory_ids: list[int],
    include_inactive: bool = False,
):
    if not memory_ids:
        return []

    placeholders = ",".join(
        "?"
        for _ in memory_ids
    )

    active_clause = (
        ""
        if include_inactive
        else "AND active = 1"
    )

    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT *
            FROM memories
            WHERE id IN ({placeholders})
            {active_clause}
            """,
            tuple(memory_ids),
        ).fetchall()

    return [
        dict(row)
        for row in rows
    ]


def get_active_memories():
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT *
            FROM memories
            WHERE active = 1
            ORDER BY id ASC
            """
        ).fetchall()

    return [
        dict(row)
        for row in rows
    ]


def get_all_memories(
    limit: int = 100,
    include_inactive: bool = False,
):
    with get_connection() as conn:
        if include_inactive:
            rows = conn.execute(
                """
                SELECT *
                FROM memories
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT *
                FROM memories
                WHERE active = 1
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

    return [
        dict(row)
        for row in rows
    ]


def get_archived_memories(
    limit: int = 100,
):
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT *
            FROM memories
            WHERE active = 0
            ORDER BY
                deleted_at DESC,
                id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [
        dict(row)
        for row in rows
    ]


# ---------------------------------------------------------------------------
# Basic SQL Search
# ---------------------------------------------------------------------------

def search_memories(
    query: str,
    limit: int = 20,
):
    query = query.strip()

    if not query:
        return []

    search_term = f"%{query}%"

    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT *
            FROM memories
            WHERE active = 1
              AND (
                    content LIKE ?
                    OR category LIKE ?
              )
            ORDER BY
                importance DESC,
                confidence DESC,
                id DESC
            LIMIT ?
            """,
            (
                search_term,
                search_term,
                limit,
            ),
        ).fetchall()

    return [
        dict(row)
        for row in rows
    ]


# ---------------------------------------------------------------------------
# Embeddings
# ---------------------------------------------------------------------------

def set_memory_embedding(
    memory_id: int,
    embedding: str,
):
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE memories
            SET
                embedding = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                embedding,
                memory_id,
            ),
        )


# ---------------------------------------------------------------------------
# Update Memory
# ---------------------------------------------------------------------------

def update_memory(
    memory_id: int,
    content: str | None = None,
    category: str | None = None,
    importance: int | None = None,
    permanence: int | None = None,
    confidence: int | None = None,
    source: str | None = None,
    embedding: str | None = None,
):
    current = get_memory(
        memory_id,
        include_inactive=True,
    )

    if not current:
        return False

    new_content = (
        content.strip()
        if content is not None
        else current["content"]
    )

    new_category = (
        category.strip().lower()
        if category is not None
        else current["category"]
    )

    new_importance = (
        max(0, min(100, int(importance)))
        if importance is not None
        else current["importance"]
    )

    new_permanence = (
        max(0, min(100, int(permanence)))
        if permanence is not None
        else current["permanence"]
    )

    new_confidence = (
        max(0, min(100, int(confidence)))
        if confidence is not None
        else current["confidence"]
    )

    new_source = (
        source.strip().lower()
        if source is not None
        else current["source"]
    )

    new_embedding = (
        embedding
        if embedding is not None
        else current["embedding"]
    )

    with get_connection() as conn:
        conn.execute(
            """
            UPDATE memories
            SET
                content = ?,
                category = ?,
                importance = ?,
                permanence = ?,
                confidence = ?,
                source = ?,
                embedding = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                new_content,
                new_category,
                new_importance,
                new_permanence,
                new_confidence,
                new_source,
                new_embedding,
                memory_id,
            ),
        )

    return True


# ---------------------------------------------------------------------------
# Soft Delete / Archive
# ---------------------------------------------------------------------------

def archive_memory(
    memory_id: int,
    superseded_by: int | None = None,
    reason: str = "forgotten",
):
    with get_connection() as conn:
        cursor = conn.execute(
            """
            UPDATE memories
            SET
                active = 0,
                deleted_at = CURRENT_TIMESTAMP,
                superseded_by = ?,
                archive_reason = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
              AND active = 1
            """,
            (
                superseded_by,
                reason,
                memory_id,
            ),
        )

        return cursor.rowcount > 0


def archive_memories(
    memory_ids: list[int],
    reason: str = "forgotten",
    superseded_by: int | None = None,
):
    archived = []

    for memory_id in memory_ids:
        if archive_memory(
            memory_id=memory_id,
            superseded_by=superseded_by,
            reason=reason,
        ):
            archived.append(memory_id)

    return archived


def restore_memory(
    memory_id: int,
):
    with get_connection() as conn:
        cursor = conn.execute(
            """
            UPDATE memories
            SET
                active = 1,
                deleted_at = NULL,
                superseded_by = NULL,
                archive_reason = NULL,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (memory_id,),
        )

        return cursor.rowcount > 0


# ---------------------------------------------------------------------------
# Permanent Delete
# ---------------------------------------------------------------------------

def permanently_delete_memory(
    memory_id: int,
):
    with get_connection() as conn:
        cursor = conn.execute(
            """
            DELETE FROM memories
            WHERE id = ?
            """,
            (memory_id,),
        )

        return cursor.rowcount > 0


# ---------------------------------------------------------------------------
# Exact Duplicate Check
# ---------------------------------------------------------------------------

def memory_exists(
    content: str,
):
    content = content.strip()

    if not content:
        return False

    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id
            FROM memories
            WHERE active = 1
              AND LOWER(content) = LOWER(?)
            LIMIT 1
            """,
            (content,),
        ).fetchone()

    return row is not None


# ---------------------------------------------------------------------------
# Compact Debug Display
# ---------------------------------------------------------------------------

def print_memory_summary(
    memory: dict,
):
    print(
        f"ID: {memory['id']}"
    )

    print(
        f"Content: {memory['content']}"
    )

    print(
        f"Category: {memory['category']}"
    )

    print(
        f"Importance: {memory['importance']}"
    )

    print(
        f"Permanence: {memory['permanence']}"
    )

    print(
        f"Confidence: {memory['confidence']}"
    )

    print(
        f"Active: {bool(memory['active'])}"
    )

    print(
        "Embedding:",
        "Yes"
        if memory.get("embedding")
        else "No",
    )

    if not memory["active"]:
        print(
            f"Archive reason: "
            f"{memory.get('archive_reason')}"
        )

        print(
            f"Superseded by: "
            f"{memory.get('superseded_by')}"
        )

    print()


# ---------------------------------------------------------------------------
# Standalone Test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    init_memory()

    print(
        "E.V.I.E. memory database ready."
    )

    print(DB_PATH)

    print(
        "\nActive memories:\n"
    )

    memories = get_all_memories()

    if not memories:
        print(
            "No active memories."
        )

    for memory in memories:
        print_memory_summary(
            memory
        )