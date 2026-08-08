"""
E.V.I.E. - Semantic Embedding Module

Created: August 8, 2026
Last Edited: August 8, 2026
Author: Max Maehara

Purpose:
    Provides local semantic embeddings for E.V.I.E.'s memory system.

How It Works:
    Uses Sentence Transformers locally to convert memory text
    and queries into normalized numeric vectors.

Most Recent Change:
    Added lazy model loading and automatic embedding backfill.
"""

import json

import numpy as np
from sentence_transformers import SentenceTransformer

from .database import (
    get_active_memories,
    set_memory_embedding,
)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

MODEL_NAME = (
    "sentence-transformers/"
    "all-MiniLM-L6-v2"
)

_embedding_model = None


# ---------------------------------------------------------------------------
# Lazy Model Loading
# ---------------------------------------------------------------------------

def get_embedding_model():
    global _embedding_model

    if _embedding_model is None:
        print(
            "Loading E.V.I.E. semantic memory model..."
        )

        _embedding_model = SentenceTransformer(
            MODEL_NAME
        )

        print(
            "Semantic memory model ready."
        )

    return _embedding_model


# ---------------------------------------------------------------------------
# Create Embedding
# ---------------------------------------------------------------------------

def create_embedding(
    text: str,
):
    text = text.strip()

    if not text:
        raise ValueError(
            "Cannot create an embedding from empty text."
        )

    model = get_embedding_model()

    vector = model.encode(
        text,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )

    return np.asarray(
        vector,
        dtype=np.float32,
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
    data: str | None,
):
    if not data:
        return None

    return np.asarray(
        json.loads(data),
        dtype=np.float32,
    )


def create_memory_embedding(
    content: str,
):
    return embedding_to_json(
        create_embedding(content)
    )


# ---------------------------------------------------------------------------
# Similarity
# ---------------------------------------------------------------------------

def semantic_similarity(
    embedding_a,
    embedding_b,
):
    return float(
        np.dot(
            embedding_a,
            embedding_b,
        )
    )


# ---------------------------------------------------------------------------
# Backfill Existing Memories
# ---------------------------------------------------------------------------

def sync_memory_embeddings():
    memories = get_active_memories()

    generated = 0

    for memory in memories:
        if memory.get("embedding"):
            continue

        embedding = create_memory_embedding(
            memory["content"]
        )

        set_memory_embedding(
            memory["id"],
            embedding,
        )

        generated += 1

    return generated


# ---------------------------------------------------------------------------
# Standalone Test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    count = sync_memory_embeddings()

    print(
        f"Generated {count} missing embeddings."
    )