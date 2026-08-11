"""
E.V.I.E. - Unified Workspace Models

Phase 12A

Purpose:
Represent the entire engineering workspace through normalized evidence,
entities, relationships, claims, and query results.

This model is intentionally source-agnostic so local files, GitHub,
Notion, PDFs, memory, Gmail, Calendar, web research, and repository
structure can all participate in the same reasoning workspace.
"""

from __future__ import annotations

from dataclasses import (
    asdict,
    dataclass,
    field,
)

from typing import Any


# ---------------------------------------------------------------------------
# Evidence Source Types
# ---------------------------------------------------------------------------

SOURCE_LOCAL_FILE = "local_file"
SOURCE_KNOWLEDGE = "knowledge_index"
SOURCE_MEMORY = "memory"
SOURCE_GITHUB = "github"
SOURCE_NOTION = "notion"
SOURCE_PDF = "pdf"
SOURCE_RESEARCH_NOTE = "research_note"
SOURCE_GMAIL = "gmail"
SOURCE_CALENDAR = "calendar"
SOURCE_WEB = "web"
SOURCE_REPOSITORY = "repository"
SOURCE_CODE = "code"
SOURCE_TEST = "test"
SOURCE_COMMIT = "commit"
SOURCE_ISSUE = "issue"
SOURCE_EXPERIMENT = "experiment"
SOURCE_HYPOTHESIS = "hypothesis"
SOURCE_DOCUMENTATION = "documentation"


# ---------------------------------------------------------------------------
# Entity Types
# ---------------------------------------------------------------------------

ENTITY_PROJECT = "project"
ENTITY_REPOSITORY = "repository"
ENTITY_MODULE = "module"
ENTITY_FILE = "file"
ENTITY_FUNCTION = "function"
ENTITY_CLASS = "class"
ENTITY_TEST = "test"
ENTITY_PROTOCOL = "protocol"
ENTITY_WORKFLOW = "workflow"
ENTITY_RESEARCH_PROJECT = "research_project"
ENTITY_PAPER = "paper"
ENTITY_HYPOTHESIS = "hypothesis"
ENTITY_EXPERIMENT = "experiment"
ENTITY_PERSON = "person"
ENTITY_TOPIC = "topic"
ENTITY_SERVICE = "service"
ENTITY_INTEGRATION = "integration"


# ---------------------------------------------------------------------------
# Relationship Types
# ---------------------------------------------------------------------------

REL_CONTAINS = "contains"
REL_IMPORTS = "imports"
REL_DEPENDS_ON = "depends_on"
REL_CALLS = "calls"
REL_TESTS = "tests"
REL_DOCUMENTS = "documents"
REL_MENTIONS = "mentions"
REL_RELATED_TO = "related_to"
REL_PRODUCES = "produces"
REL_USES = "uses"
REL_CHANGED_BY = "changed_by"
REL_SUPPORTS = "supports"
REL_CONTRADICTS = "contradicts"
REL_IMPLEMENTED_BY = "implemented_by"


# ---------------------------------------------------------------------------
# Evidence
# ---------------------------------------------------------------------------

@dataclass
class EvidenceItem:
    """
    One normalized piece of source-backed information.

    The original source payload can remain in metadata while the content
    field provides the text used for retrieval/reasoning.
    """

    evidence_id: str

    source_type: str

    source_name: str = ""

    source_id: str = ""

    title: str = ""

    content: str = ""

    uri: str = ""

    project: str = ""

    repository: str = ""

    path: str = ""

    timestamp: str = ""

    entity_ids: list[str] = field(
        default_factory=list
    )

    tags: list[str] = field(
        default_factory=list
    )

    relevance: float = 0.0

    confidence: float = 1.0

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


# ---------------------------------------------------------------------------
# Workspace Entity
# ---------------------------------------------------------------------------

@dataclass
class WorkspaceEntity:
    """
    A meaningful object in the user's engineering workspace.

    Examples:
        E.V.I.E. repository
        assistant/workflows/engine.py
        Phase 11
        BP calibration drift project
        FPGA timing closure
    """

    entity_id: str

    entity_type: str

    name: str

    canonical_name: str = ""

    project: str = ""

    repository: str = ""

    path: str = ""

    aliases: list[str] = field(
        default_factory=list
    )

    evidence_ids: list[str] = field(
        default_factory=list
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


# ---------------------------------------------------------------------------
# Relationship
# ---------------------------------------------------------------------------

@dataclass
class WorkspaceRelationship:
    relationship_id: str

    source_entity_id: str

    target_entity_id: str

    relationship_type: str

    confidence: float = 1.0

    evidence_ids: list[str] = field(
        default_factory=list
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


# ---------------------------------------------------------------------------
# Claim
# ---------------------------------------------------------------------------

@dataclass
class WorkspaceClaim:
    """
    A synthesized statement backed by one or more EvidenceItems.
    """

    claim_id: str

    text: str

    evidence_ids: list[str] = field(
        default_factory=list
    )

    confidence: float = 0.0

    entity_ids: list[str] = field(
        default_factory=list
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


# ---------------------------------------------------------------------------
# Query
# ---------------------------------------------------------------------------

@dataclass
class WorkspaceQuery:
    query: str

    project: str = ""

    repository: str = ""

    entity_ids: list[str] = field(
        default_factory=list
    )

    source_types: list[str] = field(
        default_factory=list
    )

    limit: int = 30

    include_code: bool = True

    include_memory: bool = True

    include_external: bool = True

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------

@dataclass
class WorkspaceResult:
    query: str

    evidence: list[EvidenceItem] = field(
        default_factory=list
    )

    entities: list[WorkspaceEntity] = field(
        default_factory=list
    )

    relationships: list[WorkspaceRelationship] = field(
        default_factory=list
    )

    claims: list[WorkspaceClaim] = field(
        default_factory=list
    )

    answer: str = ""

    confidence: float = 0.0

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------

def evidence_to_dict(
    item: EvidenceItem,
):
    return asdict(
        item
    )


def entity_to_dict(
    item: WorkspaceEntity,
):
    return asdict(
        item
    )


def relationship_to_dict(
    item: WorkspaceRelationship,
):
    return asdict(
        item
    )


def claim_to_dict(
    item: WorkspaceClaim,
):
    return asdict(
        item
    )


def query_to_dict(
    item: WorkspaceQuery,
):
    return asdict(
        item
    )


def result_to_dict(
    item: WorkspaceResult,
):
    return asdict(
        item
    )


# ---------------------------------------------------------------------------
# Deserialization
# ---------------------------------------------------------------------------

def evidence_from_dict(
    data: dict,
):
    return EvidenceItem(
        evidence_id=str(
            data.get(
                "evidence_id",
                "",
            )
            or ""
        ),

        source_type=str(
            data.get(
                "source_type",
                "",
            )
            or ""
        ),

        source_name=str(
            data.get(
                "source_name",
                "",
            )
            or ""
        ),

        source_id=str(
            data.get(
                "source_id",
                "",
            )
            or ""
        ),

        title=str(
            data.get(
                "title",
                "",
            )
            or ""
        ),

        content=str(
            data.get(
                "content",
                "",
            )
            or ""
        ),

        uri=str(
            data.get(
                "uri",
                "",
            )
            or ""
        ),

        project=str(
            data.get(
                "project",
                "",
            )
            or ""
        ),

        repository=str(
            data.get(
                "repository",
                "",
            )
            or ""
        ),

        path=str(
            data.get(
                "path",
                "",
            )
            or ""
        ),

        timestamp=str(
            data.get(
                "timestamp",
                "",
            )
            or ""
        ),

        entity_ids=[
            str(
                value
            )
            for value
            in (
                data.get(
                    "entity_ids",
                    [],
                )
                or []
            )
        ],

        tags=[
            str(
                value
            )
            for value
            in (
                data.get(
                    "tags",
                    [],
                )
                or []
            )
        ],

        relevance=float(
            data.get(
                "relevance",
                0.0,
            )
            or 0.0
        ),

        confidence=float(
            data.get(
                "confidence",
                1.0,
            )
            or 0.0
        ),

        metadata=(
            data.get(
                "metadata",
                {},
            )
            if isinstance(
                data.get(
                    "metadata",
                    {},
                ),
                dict,
            )
            else {}
        ),
    )


def entity_from_dict(
    data: dict,
):
    return WorkspaceEntity(
        entity_id=str(
            data.get(
                "entity_id",
                "",
            )
            or ""
        ),

        entity_type=str(
            data.get(
                "entity_type",
                "",
            )
            or ""
        ),

        name=str(
            data.get(
                "name",
                "",
            )
            or ""
        ),

        canonical_name=str(
            data.get(
                "canonical_name",
                "",
            )
            or ""
        ),

        project=str(
            data.get(
                "project",
                "",
            )
            or ""
        ),

        repository=str(
            data.get(
                "repository",
                "",
            )
            or ""
        ),

        path=str(
            data.get(
                "path",
                "",
            )
            or ""
        ),

        aliases=[
            str(
                value
            )
            for value
            in (
                data.get(
                    "aliases",
                    [],
                )
                or []
            )
        ],

        evidence_ids=[
            str(
                value
            )
            for value
            in (
                data.get(
                    "evidence_ids",
                    [],
                )
                or []
            )
        ],

        metadata=(
            data.get(
                "metadata",
                {},
            )
            if isinstance(
                data.get(
                    "metadata",
                    {},
                ),
                dict,
            )
            else {}
        ),
    )


def relationship_from_dict(
    data: dict,
):
    return WorkspaceRelationship(
        relationship_id=str(
            data.get(
                "relationship_id",
                "",
            )
            or ""
        ),

        source_entity_id=str(
            data.get(
                "source_entity_id",
                "",
            )
            or ""
        ),

        target_entity_id=str(
            data.get(
                "target_entity_id",
                "",
            )
            or ""
        ),

        relationship_type=str(
            data.get(
                "relationship_type",
                "",
            )
            or ""
        ),

        confidence=float(
            data.get(
                "confidence",
                1.0,
            )
            or 0.0
        ),

        evidence_ids=[
            str(
                value
            )
            for value
            in (
                data.get(
                    "evidence_ids",
                    [],
                )
                or []
            )
        ],

        metadata=(
            data.get(
                "metadata",
                {},
            )
            if isinstance(
                data.get(
                    "metadata",
                    {},
                ),
                dict,
            )
            else {}
        ),
    )


def claim_from_dict(
    data: dict,
):
    return WorkspaceClaim(
        claim_id=str(
            data.get(
                "claim_id",
                "",
            )
            or ""
        ),

        text=str(
            data.get(
                "text",
                "",
            )
            or ""
        ),

        evidence_ids=[
            str(
                value
            )
            for value
            in (
                data.get(
                    "evidence_ids",
                    [],
                )
                or []
            )
        ],

        confidence=float(
            data.get(
                "confidence",
                0.0,
            )
            or 0.0
        ),

        entity_ids=[
            str(
                value
            )
            for value
            in (
                data.get(
                    "entity_ids",
                    [],
                )
                or []
            )
        ],

        metadata=(
            data.get(
                "metadata",
                {},
            )
            if isinstance(
                data.get(
                    "metadata",
                    {},
                ),
                dict,
            )
            else {}
        ),
    )
