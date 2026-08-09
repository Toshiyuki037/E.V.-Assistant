"""
E.V.I.E. - Knowledge Database

Created: August 8, 2026
Last Edited: August 8, 2026
Author: Max Maehara

Purpose:
    Stores indexed project files, searchable chunks, embeddings,
    and metadata for E.V.I.E.'s local project knowledge system.

How It Works:
    Uses a local SQLite database separate from E.V.I.E.'s memory DB.

    Stores:
        - indexed files
        - file hashes
        - structured code/document chunks
        - semantic embeddings
        - line ranges
        - symbols
        - workspace ownership

Most Recent Change:
    Added neighboring-chunk retrieval for cross-file and
    execution-flow context expansion.
"""

import sqlite3
from pathlib import Path


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT = (
    Path(__file__)
    .resolve()
    .parent
    .parent
    .parent
)

DB_PATH = (
    ROOT
    / "knowledge"
    / "knowledge.db"
)

DB_PATH.parent.mkdir(
    exist_ok=True
)


# ---------------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------------

def get_connection():

    conn = sqlite3.connect(
        DB_PATH
    )

    conn.row_factory = sqlite3.Row

    return conn


# ---------------------------------------------------------------------------
# Initialize
# ---------------------------------------------------------------------------

def init_knowledge_database():

    with get_connection() as conn:

        conn.execute(
            """
            PRAGMA foreign_keys = ON
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                workspace_path TEXT NOT NULL,

                relative_path TEXT NOT NULL,

                filename TEXT NOT NULL,

                extension TEXT,

                file_type TEXT,

                size_bytes INTEGER,

                modified_time REAL,

                file_hash TEXT NOT NULL,

                indexed_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP,

                UNIQUE(
                    workspace_path,
                    relative_path
                )
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                file_id INTEGER NOT NULL,

                workspace_path TEXT NOT NULL,

                relative_path TEXT NOT NULL,

                chunk_index INTEGER NOT NULL,

                chunk_type TEXT,

                symbol TEXT,

                start_line INTEGER,

                end_line INTEGER,

                content TEXT NOT NULL,

                embedding TEXT,

                created_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY(file_id)
                    REFERENCES files(id)
                    ON DELETE CASCADE
            )
            """
        )

        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_chunks_workspace

            ON chunks(workspace_path)
            """
        )

        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_chunks_path

            ON chunks(
                workspace_path,
                relative_path
            )
            """
        )

        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_chunks_location

            ON chunks(
                workspace_path,
                relative_path,
                chunk_index
            )
            """
        )


# ---------------------------------------------------------------------------
# File Operations
# ---------------------------------------------------------------------------

def get_file_record(
    workspace_path: str,
    relative_path: str,
):

    with get_connection() as conn:

        row = conn.execute(
            """
            SELECT *
            FROM files

            WHERE workspace_path = ?
              AND relative_path = ?

            LIMIT 1
            """,
            (
                workspace_path,
                relative_path,
            ),
        ).fetchone()

    return (
        dict(row)
        if row
        else None
    )


def upsert_file(
    workspace_path: str,
    file_data: dict,
    file_hash: str,
):

    with get_connection() as conn:

        conn.execute(
            """
            INSERT INTO files (
                workspace_path,
                relative_path,
                filename,
                extension,
                file_type,
                size_bytes,
                modified_time,
                file_hash,
                indexed_at
            )

            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?,
                CURRENT_TIMESTAMP
            )

            ON CONFLICT(
                workspace_path,
                relative_path
            )

            DO UPDATE SET
                filename =
                    excluded.filename,

                extension =
                    excluded.extension,

                file_type =
                    excluded.file_type,

                size_bytes =
                    excluded.size_bytes,

                modified_time =
                    excluded.modified_time,

                file_hash =
                    excluded.file_hash,

                indexed_at =
                    CURRENT_TIMESTAMP
            """,
            (
                workspace_path,

                file_data[
                    "relative_path"
                ],

                file_data[
                    "filename"
                ],

                file_data[
                    "extension"
                ],

                file_data[
                    "file_type"
                ],

                file_data[
                    "size_bytes"
                ],

                file_data.get(
                    "modified_time"
                ),

                file_hash,
            ),
        )

    record = get_file_record(
        workspace_path,
        file_data[
            "relative_path"
        ],
    )

    return (
        record["id"]
        if record
        else None
    )


def delete_file_chunks(
    file_id: int,
):

    with get_connection() as conn:

        conn.execute(
            """
            DELETE FROM chunks
            WHERE file_id = ?
            """,
            (file_id,),
        )


def delete_file_record(
    file_id: int,
):

    with get_connection() as conn:

        conn.execute(
            """
            DELETE FROM chunks
            WHERE file_id = ?
            """,
            (file_id,),
        )

        conn.execute(
            """
            DELETE FROM files
            WHERE id = ?
            """,
            (file_id,),
        )


# ---------------------------------------------------------------------------
# Chunk Operations
# ---------------------------------------------------------------------------

def insert_chunk(
    file_id: int,
    workspace_path: str,
    chunk: dict,
    embedding: str,
):

    with get_connection() as conn:

        cursor = conn.execute(
            """
            INSERT INTO chunks (
                file_id,
                workspace_path,
                relative_path,
                chunk_index,
                chunk_type,
                symbol,
                start_line,
                end_line,
                content,
                embedding
            )

            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            """,
            (
                file_id,
                workspace_path,

                chunk[
                    "relative_path"
                ],

                chunk[
                    "chunk_index"
                ],

                chunk[
                    "chunk_type"
                ],

                chunk.get(
                    "symbol"
                ),

                chunk[
                    "start_line"
                ],

                chunk[
                    "end_line"
                ],

                chunk[
                    "content"
                ],

                embedding,
            ),
        )

        return cursor.lastrowid


def get_chunk(
    workspace_path: str,
    relative_path: str,
    chunk_index: int,
):
    """
    Retrieves one exact indexed chunk.
    """

    with get_connection() as conn:

        row = conn.execute(
            """
            SELECT *
            FROM chunks

            WHERE workspace_path = ?
              AND relative_path = ?
              AND chunk_index = ?

            LIMIT 1
            """,
            (
                workspace_path,
                relative_path,
                chunk_index,
            ),
        ).fetchone()

    return (
        dict(row)
        if row
        else None
    )


# ---------------------------------------------------------------------------
# Neighbor Retrieval
# ---------------------------------------------------------------------------

def get_neighbor_chunks(
    workspace_path: str,
    relative_path: str,
    chunk_index: int,
    before: int = 1,
    after: int = 1,
):
    """
    Returns chunks around a matched chunk.

    Example:

        matched chunk = 7

        before = 1
        after = 1

        returns:
            6
            7
            8

    This allows semantic retrieval to surface the best-matching
    region while still giving the reasoning model enough surrounding
    implementation to understand execution flow.
    """

    first_index = max(
        0,
        chunk_index - before,
    )

    last_index = (
        chunk_index
        + after
    )

    with get_connection() as conn:

        rows = conn.execute(
            """
            SELECT *
            FROM chunks

            WHERE workspace_path = ?
              AND relative_path = ?
              AND chunk_index
                  BETWEEN ? AND ?

            ORDER BY chunk_index ASC
            """,
            (
                workspace_path,
                relative_path,
                first_index,
                last_index,
            ),
        ).fetchall()

    return [
        dict(row)
        for row in rows
    ]


# ---------------------------------------------------------------------------
# Workspace Operations
# ---------------------------------------------------------------------------

def get_workspace_files(
    workspace_path: str,
):

    with get_connection() as conn:

        rows = conn.execute(
            """
            SELECT *
            FROM files

            WHERE workspace_path = ?

            ORDER BY relative_path
            """,
            (workspace_path,),
        ).fetchall()

    return [
        dict(row)
        for row in rows
    ]


def get_workspace_chunks(
    workspace_path: str,
):

    with get_connection() as conn:

        rows = conn.execute(
            """
            SELECT *
            FROM chunks

            WHERE workspace_path = ?

            ORDER BY
                relative_path,
                chunk_index
            """,
            (workspace_path,),
        ).fetchall()

    return [
        dict(row)
        for row in rows
    ]


def workspace_chunk_count(
    workspace_path: str,
):

    with get_connection() as conn:

        row = conn.execute(
            """
            SELECT
                COUNT(*) AS count

            FROM chunks

            WHERE workspace_path = ?
            """,
            (workspace_path,),
        ).fetchone()

    return (
        row["count"]
        if row
        else 0
    )


# ---------------------------------------------------------------------------
# Test
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    init_knowledge_database()

    print(
        "E.V.I.E. knowledge database ready."
    )

    print(
        DB_PATH
    )