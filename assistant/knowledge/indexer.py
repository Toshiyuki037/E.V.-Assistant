"""
E.V.I.E. - Knowledge Indexer

Created: August 8, 2026
Last Edited: August 8, 2026
Author: Max Maehara

Purpose:
    Converts the active workspace into persistent searchable knowledge.

How It Works:
    Scans files, hashes them, detects changes, reads changed files,
    chunks them, embeds chunks locally, and stores everything in SQLite.

Most Recent Change:
    Initial incremental repository indexing system.
"""

import hashlib
from pathlib import Path

from .chunker import (
    chunk_file,
)

from .database import (
    delete_file_chunks,
    delete_file_record,
    get_file_record,
    get_workspace_files,
    init_knowledge_database,
    insert_chunk,
    upsert_file,
)

from .embeddings import (
    create_knowledge_embedding,
)

from .reader import (
    read_file,
)

from .scanner import (
    get_active_workspace_path,
    scan_workspace,
)


# ---------------------------------------------------------------------------
# Hashing
# ---------------------------------------------------------------------------

def calculate_file_hash(
    path: str | Path,
):

    sha256 = hashlib.sha256()

    with open(
        path,
        "rb",
    ) as file:

        while True:

            block = file.read(
                65536
            )

            if not block:
                break

            sha256.update(
                block
            )

    return sha256.hexdigest()


# ---------------------------------------------------------------------------
# Index One File
# ---------------------------------------------------------------------------

def index_file(
    workspace: Path,
    scanned_file: dict,
):

    absolute_path = Path(
        scanned_file[
            "absolute_path"
        ]
    )

    file_hash = calculate_file_hash(
        absolute_path
    )

    existing = get_file_record(
        str(workspace),
        scanned_file[
            "relative_path"
        ],
    )

    if (
        existing
        and existing[
            "file_hash"
        ]
        == file_hash
    ):

        return {
            "status": "unchanged",
            "chunks": 0,
        }

    file_data = read_file(
        absolute_path,
        workspace,
    )

    if not file_data[
        "success"
    ]:

        return {
            "status": "failed",
            "chunks": 0,
            "error":
                file_data.get(
                    "error"
                ),
        }

    # Scanner knows modification time.
    file_data["modified_time"] = (
        scanned_file[
            "modified_time"
        ]
    )

    chunks = chunk_file(
        file_data
    )

    file_id = upsert_file(
        workspace_path=str(
            workspace
        ),
        file_data=file_data,
        file_hash=file_hash,
    )

    if file_id is None:

        return {
            "status": "failed",
            "chunks": 0,
            "error":
                "Unable to create file record.",
        }

    delete_file_chunks(
        file_id
    )

    created = 0

    for chunk in chunks:

        embedding_text = (
            f"File: "
            f"{chunk['relative_path']}\n"

            f"Type: "
            f"{chunk['file_type']}\n"

            f"Symbol: "
            f"{chunk.get('symbol') or ''}\n\n"

            f"{chunk['content']}"
        )

        embedding = (
            create_knowledge_embedding(
                embedding_text
            )
        )

        insert_chunk(
            file_id=file_id,
            workspace_path=str(
                workspace
            ),
            chunk=chunk,
            embedding=embedding,
        )

        created += 1

    return {
        "status": "indexed",
        "chunks": created,
    }


# ---------------------------------------------------------------------------
# Remove Deleted Files
# ---------------------------------------------------------------------------

def remove_missing_files(
    workspace: Path,
    current_files: list[dict],
):

    current_paths = {
        file["relative_path"]
        for file in current_files
    }

    indexed_files = (
        get_workspace_files(
            str(workspace)
        )
    )

    removed = 0

    for record in indexed_files:

        if (
            record["relative_path"]
            in current_paths
        ):
            continue

        delete_file_record(
            record["id"]
        )

        removed += 1

    return removed


# ---------------------------------------------------------------------------
# Index Workspace
# ---------------------------------------------------------------------------

def index_workspace(
    workspace_path=None,
):

    init_knowledge_database()

    if workspace_path is None:

        workspace = (
            get_active_workspace_path()
        )

    else:

        workspace = Path(
            workspace_path
        ).resolve()

    if workspace is None:

        return {
            "success": False,
            "error":
                "No active workspace.",
        }

    files = scan_workspace(
        workspace
    )

    statistics = {
        "success": True,

        "workspace":
            str(workspace),

        "files_discovered":
            len(files),

        "files_indexed":
            0,

        "files_unchanged":
            0,

        "files_failed":
            0,

        "files_removed":
            0,

        "chunks_created":
            0,
    }

    for file in files:

        result = index_file(
            workspace,
            file,
        )

        status = result[
            "status"
        ]

        if status == "indexed":

            statistics[
                "files_indexed"
            ] += 1

            statistics[
                "chunks_created"
            ] += result[
                "chunks"
            ]

        elif status == "unchanged":

            statistics[
                "files_unchanged"
            ] += 1

        else:

            statistics[
                "files_failed"
            ] += 1

    statistics[
        "files_removed"
    ] = remove_missing_files(
        workspace,
        files,
    )

    return statistics


# ---------------------------------------------------------------------------
# Standalone
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    print(
        "E.V.I.E. Knowledge Indexer"
    )

    print(
        "---------------------------"
    )

    result = index_workspace()

    if not result[
        "success"
    ]:

        print(
            "Index failed:",
            result["error"],
        )

        raise SystemExit(1)

    print(
        "Workspace:",
        result["workspace"],
    )

    print(
        "Files discovered:",
        result[
            "files_discovered"
        ],
    )

    print(
        "Files indexed:",
        result[
            "files_indexed"
        ],
    )

    print(
        "Files unchanged:",
        result[
            "files_unchanged"
        ],
    )

    print(
        "Files removed:",
        result[
            "files_removed"
        ],
    )

    print(
        "Files failed:",
        result[
            "files_failed"
        ],
    )

    print(
        "Chunks created:",
        result[
            "chunks_created"
        ],
    )