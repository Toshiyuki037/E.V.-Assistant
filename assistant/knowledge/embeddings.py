"""
E.V.I.E. - Knowledge Embeddings

Created: August 8, 2026
Last Edited: August 8, 2026
Author: Max Maehara

Purpose:
    Provides local semantic vectors for code/document knowledge chunks.

Most Recent Change:
    Initial Phase 4 local embedding interface.
"""

import json

import numpy as np


# ---------------------------------------------------------------------------
# Reuse E.V.I.E.'s existing embedding model
# ---------------------------------------------------------------------------

try:

    from ..memory.embeddings import (
        create_embedding,
    )

except ImportError:

    from memory.embeddings import (
        create_embedding,
    )


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------

def embedding_to_json(
    embedding,
):

    return json.dumps(
        embedding.tolist()
    )


def embedding_from_json(
    value: str | None,
):

    if not value:
        return None

    return np.asarray(
        json.loads(value),
        dtype=np.float32,
    )


# ---------------------------------------------------------------------------
# Knowledge Embedding
# ---------------------------------------------------------------------------

def create_knowledge_embedding(
    text: str,
):

    vector = create_embedding(
        text
    )

    return embedding_to_json(
        vector
    )


def similarity(
    first,
    second,
):

    return float(
        np.dot(
            first,
            second,
        )
    )