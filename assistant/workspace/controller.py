"""
E.V.I.E. - Unified Workspace Controller

Phase 12A

Purpose:
Public interface for creating normalized evidence, entities, and
relationships.

Later adapters will call this controller rather than writing directly
to the store.
"""

from __future__ import annotations

import hashlib

from typing import Any

from .evidence import (
    list_entities,
    list_evidence,
    list_relationships,
    load_entity,
    load_evidence,
    load_relationship,
    save_entity,
    save_evidence,
    save_relationship,
)

from .models import (
    EvidenceItem,
    WorkspaceEntity,
    WorkspaceRelationship,
)


# ---------------------------------------------------------------------------
# Stable IDs
# ---------------------------------------------------------------------------

def _stable_hash(
    *values,
):
    joined = (
        "\x1f".join(
            str(
                value
                or ""
            )
            for value
            in values
        )
    )

    return (
        hashlib.sha256(
            joined.encode(
                "utf-8"
            )
        )
        .hexdigest()[
            :16
        ]
    )


def new_evidence_id(
    source_type: str,
    source_id: str,
    content: str = "",
):
    return (
        f"ev:{source_type}:"
        + _stable_hash(
            source_type,
            source_id,
            content,
        )
    )


def new_entity_id(
    entity_type: str,
    name: str,
    *,
    repository: str = "",
    path: str = "",
):
    return (
        f"entity:{entity_type}:"
        + _stable_hash(
            entity_type,
            name,
            repository,
            path,
        )
    )


def new_relationship_id(
    source_entity_id: str,
    target_entity_id: str,
    relationship_type: str,
):
    return (
        "rel:"
        + _stable_hash(
            source_entity_id,
            target_entity_id,
            relationship_type,
        )
    )


# ---------------------------------------------------------------------------
# Evidence Creation
# ---------------------------------------------------------------------------

def create_evidence(
    *,
    source_type: str,
    source_name: str = "",
    source_id: str = "",
    title: str = "",
    content: str = "",
    uri: str = "",
    project: str = "",
    repository: str = "",
    path: str = "",
    timestamp: str = "",
    entity_ids: list[str] | None = None,
    tags: list[str] | None = None,
    relevance: float = 0.0,
    confidence: float = 1.0,
    metadata: dict[str, Any] | None = None,
    evidence_id: str | None = None,
):
    evidence_id = (
        evidence_id
        or new_evidence_id(
            source_type,
            source_id
            or uri
            or path
            or title,
            content,
        )
    )

    item = EvidenceItem(
        evidence_id=
            evidence_id,

        source_type=
            str(
                source_type
                or ""
            ),

        source_name=
            str(
                source_name
                or ""
            ),

        source_id=
            str(
                source_id
                or ""
            ),

        title=
            str(
                title
                or ""
            ),

        content=
            str(
                content
                or ""
            ),

        uri=
            str(
                uri
                or ""
            ),

        project=
            str(
                project
                or ""
            ),

        repository=
            str(
                repository
                or ""
            ),

        path=
            str(
                path
                or ""
            ),

        timestamp=
            str(
                timestamp
                or ""
            ),

        entity_ids=[
            str(
                item
            )
            for item
            in (
                entity_ids
                or []
            )
        ],

        tags=[
            str(
                item
            )
            for item
            in (
                tags
                or []
            )
        ],

        relevance=float(
            relevance
            or 0.0
        ),

        confidence=float(
            confidence
            if confidence is not None
            else 1.0
        ),

        metadata=(
            metadata
            if isinstance(
                metadata,
                dict,
            )
            else {}
        ),
    )

    return save_evidence(
        item
    )


# ---------------------------------------------------------------------------
# Entity Creation
# ---------------------------------------------------------------------------

def create_entity(
    *,
    entity_type: str,
    name: str,
    canonical_name: str = "",
    project: str = "",
    repository: str = "",
    path: str = "",
    aliases: list[str] | None = None,
    evidence_ids: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
    entity_id: str | None = None,
):
    entity_id = (
        entity_id
        or new_entity_id(
            entity_type,
            name,
            repository=repository,
            path=path,
        )
    )

    item = WorkspaceEntity(
        entity_id=
            entity_id,

        entity_type=
            str(
                entity_type
                or ""
            ),

        name=
            str(
                name
                or ""
            ),

        canonical_name=
            str(
                canonical_name
                or name
                or ""
            ),

        project=
            str(
                project
                or ""
            ),

        repository=
            str(
                repository
                or ""
            ),

        path=
            str(
                path
                or ""
            ),

        aliases=[
            str(
                item
            )
            for item
            in (
                aliases
                or []
            )
        ],

        evidence_ids=[
            str(
                item
            )
            for item
            in (
                evidence_ids
                or []
            )
        ],

        metadata=(
            metadata
            if isinstance(
                metadata,
                dict,
            )
            else {}
        ),
    )

    return save_entity(
        item
    )


# ---------------------------------------------------------------------------
# Relationship Creation
# ---------------------------------------------------------------------------

def create_relationship(
    *,
    source_entity_id: str,
    target_entity_id: str,
    relationship_type: str,
    confidence: float = 1.0,
    evidence_ids: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
    relationship_id: str | None = None,
):
    relationship_id = (
        relationship_id
        or new_relationship_id(
            source_entity_id,
            target_entity_id,
            relationship_type,
        )
    )

    item = WorkspaceRelationship(
        relationship_id=
            relationship_id,

        source_entity_id=
            str(
                source_entity_id
            ),

        target_entity_id=
            str(
                target_entity_id
            ),

        relationship_type=
            str(
                relationship_type
            ),

        confidence=float(
            confidence
            if confidence is not None
            else 1.0
        ),

        evidence_ids=[
            str(
                item
            )
            for item
            in (
                evidence_ids
                or []
            )
        ],

        metadata=(
            metadata
            if isinstance(
                metadata,
                dict,
            )
            else {}
        ),
    )

    return save_relationship(
        item
    )


# ---------------------------------------------------------------------------
# Public Reads
# ---------------------------------------------------------------------------

def get_evidence(
    evidence_id: str,
):
    return load_evidence(
        evidence_id
    )


def get_entity(
    entity_id: str,
):
    return load_entity(
        entity_id
    )


def get_relationship(
    relationship_id: str,
):
    return load_relationship(
        relationship_id
    )


def get_all_evidence():
    return list_evidence()


def get_all_entities():
    return list_entities()


def get_all_relationships():
    return list_relationships()
