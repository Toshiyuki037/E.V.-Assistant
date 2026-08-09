"""
E.V.I.E. - Knowledge Chunker

Created: August 8, 2026
Last Edited: August 8, 2026
Author: Max Maehara

Purpose:
    Breaks source files and documents into searchable knowledge chunks.

How It Works:
    Python files are analyzed using the AST.

    Small functions/classes remain whole semantic chunks.

    Large functions/classes are divided into overlapping subchunks so
    code near the end of large functions is never lost.

    Other supported files use overlapping line-based chunks.

Most Recent Change:
    Added large-symbol subchunking to prevent long functions from being
    truncated and losing searchable implementation details.
"""

import ast


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

GENERIC_CHUNK_LINES = 80
GENERIC_OVERLAP_LINES = 15

SYMBOL_CHUNK_LINES = 70
SYMBOL_OVERLAP_LINES = 15

MAX_CHUNK_CHARACTERS = 8000


# ---------------------------------------------------------------------------
# Basic Chunk Builder
# ---------------------------------------------------------------------------

def make_chunk(
    content: str,
    start_line: int,
    end_line: int,
    chunk_type: str,
    symbol: str | None = None,
):
    content = content.strip()

    if not content:
        return None

    return {
        "content": content,
        "start_line": start_line,
        "end_line": end_line,
        "chunk_type": chunk_type,
        "symbol": symbol,
    }


# ---------------------------------------------------------------------------
# Generic Line Chunking
# ---------------------------------------------------------------------------

def chunk_line_range(
    lines: list[str],
    first_line: int,
    last_line: int,
    chunk_type: str,
    symbol: str | None = None,
    chunk_lines: int = GENERIC_CHUNK_LINES,
    overlap_lines: int = GENERIC_OVERLAP_LINES,
):
    """
    Splits a known line range into overlapping chunks.

    first_line and last_line are 1-based and inclusive.
    """

    chunks = []

    start_line = first_line

    while start_line <= last_line:

        end_line = min(
            start_line + chunk_lines - 1,
            last_line,
        )

        content = "\n".join(
            lines[
                start_line - 1:
                end_line
            ]
        )

        # If an unusually dense chunk still exceeds the character
        # safeguard, reduce it until it fits.
        while (
            len(content) > MAX_CHUNK_CHARACTERS
            and end_line > start_line
        ):
            reduction = max(
                1,
                (end_line - start_line) // 4,
            )

            end_line -= reduction

            content = "\n".join(
                lines[
                    start_line - 1:
                    end_line
                ]
            )

        chunk = make_chunk(
            content=content,
            start_line=start_line,
            end_line=end_line,
            chunk_type=chunk_type,
            symbol=symbol,
        )

        if chunk:
            chunks.append(chunk)

        if end_line >= last_line:
            break

        start_line = max(
            end_line - overlap_lines + 1,
            start_line + 1,
        )

    return chunks


def chunk_by_lines(
    content: str,
):
    lines = content.splitlines()

    if not lines:
        return []

    return chunk_line_range(
        lines=lines,
        first_line=1,
        last_line=len(lines),
        chunk_type="text",
        symbol=None,
        chunk_lines=GENERIC_CHUNK_LINES,
        overlap_lines=GENERIC_OVERLAP_LINES,
    )


# ---------------------------------------------------------------------------
# Python Symbol Chunking
# ---------------------------------------------------------------------------

def chunk_python_symbol(
    lines: list[str],
    node,
):
    """
    Keeps a small symbol whole.

    Large functions/classes are split into overlapping chunks while
    retaining the same symbol name.
    """

    start_line = node.lineno

    end_line = getattr(
        node,
        "end_lineno",
        start_line,
    )

    if isinstance(
        node,
        ast.ClassDef,
    ):
        chunk_type = "class"

    else:
        chunk_type = "function"

    full_content = "\n".join(
        lines[
            start_line - 1:
            end_line
        ]
    )

    # Small function/class: preserve as one semantic chunk.
    if (
        len(full_content) <= MAX_CHUNK_CHARACTERS
        and (
            end_line - start_line + 1
            <= SYMBOL_CHUNK_LINES
        )
    ):
        chunk = make_chunk(
            content=full_content,
            start_line=start_line,
            end_line=end_line,
            chunk_type=chunk_type,
            symbol=node.name,
        )

        return (
            [chunk]
            if chunk
            else []
        )

    # Large symbol: split without losing later implementation.
    return chunk_line_range(
        lines=lines,
        first_line=start_line,
        last_line=end_line,
        chunk_type=(
            f"{chunk_type}_part"
        ),
        symbol=node.name,
        chunk_lines=SYMBOL_CHUNK_LINES,
        overlap_lines=SYMBOL_OVERLAP_LINES,
    )


# ---------------------------------------------------------------------------
# Python AST Chunking
# ---------------------------------------------------------------------------

def chunk_python(
    content: str,
):
    lines = content.splitlines()

    try:
        tree = ast.parse(
            content
        )

    except SyntaxError:
        return chunk_by_lines(
            content
        )

    chunks = []

    top_level_nodes = [
        node
        for node in tree.body
        if isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
                ast.ClassDef,
            ),
        )
    ]

    # -----------------------------------------------------------------------
    # Module Preamble
    # -----------------------------------------------------------------------

    first_symbol_line = min(
        (
            node.lineno
            for node in top_level_nodes
        ),
        default=len(lines) + 1,
    )

    if first_symbol_line > 1:

        preamble_end = (
            first_symbol_line - 1
        )

        chunks.extend(
            chunk_line_range(
                lines=lines,
                first_line=1,
                last_line=preamble_end,
                chunk_type="module",
                symbol=None,
                chunk_lines=GENERIC_CHUNK_LINES,
                overlap_lines=GENERIC_OVERLAP_LINES,
            )
        )

    # -----------------------------------------------------------------------
    # Functions / Classes
    # -----------------------------------------------------------------------

    for node in top_level_nodes:

        chunks.extend(
            chunk_python_symbol(
                lines,
                node,
            )
        )

    if not chunks:
        return chunk_by_lines(
            content
        )

    return chunks


# ---------------------------------------------------------------------------
# Main File Chunker
# ---------------------------------------------------------------------------

def chunk_file(
    file_data: dict,
):
    if not file_data.get(
        "success"
    ):
        return []

    content = file_data.get(
        "content",
        "",
    )

    extension = (
        file_data.get(
            "extension",
            "",
        )
        .lower()
    )

    if extension == ".py":

        chunks = chunk_python(
            content
        )

    else:

        chunks = chunk_by_lines(
            content
        )

    final = []

    for index, chunk in enumerate(
        chunks
    ):

        item = dict(
            chunk
        )

        item["chunk_index"] = (
            index
        )

        item["relative_path"] = (
            file_data[
                "relative_path"
            ]
        )

        item["filename"] = (
            file_data[
                "filename"
            ]
        )

        item["file_type"] = (
            file_data[
                "file_type"
            ]
        )

        final.append(
            item
        )

    return final


# ---------------------------------------------------------------------------
# Standalone Test
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    from .reader import (
        read_file,
    )

    result = read_file(
        "assistant/main.py"
    )

    if not result["success"]:

        print(
            "Read failed:",
            result["error"],
        )

        raise SystemExit(1)

    chunks = chunk_file(
        result
    )

    print(
        "E.V.I.E. Knowledge Chunker"
    )

    print(
        "---------------------------"
    )

    print(
        "File:",
        result["relative_path"],
    )

    print(
        "Chunks:",
        len(chunks),
    )

    for chunk in chunks:

        print()

        print(
            f"[{chunk['chunk_index']}] "
            f"{chunk['chunk_type']}"
        )

        print(
            "Symbol:",
            chunk[
                "symbol"
            ],
        )

        print(
            "Lines:",
            chunk[
                "start_line"
            ],
            "-",
            chunk[
                "end_line"
            ],
        )