"""
Phase 12D cross-source query tests.
"""

from assistant.workspace.models import (
    EvidenceItem,
    WorkspaceQuery,
)
from assistant.workspace.ranking import (
    rank_evidence,
)
from assistant.workspace.query import (
    _dedupe,
)


def test_ranking_prefers_query_overlap():
    evidence = [
        EvidenceItem(
            evidence_id="a",
            source_type="local_file",
            title="Unrelated",
            content="weather protocol",
        ),
        EvidenceItem(
            evidence_id="b",
            source_type="github",
            title="Timing closure",
            content="FPGA timing closure dependency",
        ),
    ]

    ranked = rank_evidence(
        "FPGA timing closure",
        evidence,
    )

    assert ranked[0].evidence_id == "b"


def test_dedupe_removes_duplicate_source_payload():
    items = [
        EvidenceItem(
            evidence_id="a",
            source_type="github",
            source_id="commit",
            content="same",
        ),
        EvidenceItem(
            evidence_id="b",
            source_type="github",
            source_id="commit",
            content="same",
        ),
    ]

    deduped = _dedupe(
        items
    )

    assert len(deduped) == 1
