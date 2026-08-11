"""
Phase 12D source diversity tests.
"""

from assistant.workspace.models import (
    EvidenceItem,
)
from assistant.workspace.query import (
    _balanced_select,
)
from assistant.workspace.adapters.notion import (
    _collect_page_titles,
)


def test_balanced_selection_preserves_multiple_sources():
    evidence = []

    for index in range(10):
        evidence.append(
            EvidenceItem(
                evidence_id=f"code-{index}",
                source_type="code",
                source_id=f"code-{index}",
                content="phase 11 workflows",
                relevance=10.0 - index,
            )
        )

    evidence.append(
        EvidenceItem(
            evidence_id="github-1",
            source_type="github",
            source_id="github-1",
            content="Phase 11 commit",
            relevance=2.0,
        )
    )

    evidence.append(
        EvidenceItem(
            evidence_id="notion-1",
            source_type="notion",
            source_id="notion-1",
            content="Phase 11 documentation",
            relevance=2.0,
        )
    )

    selected = _balanced_select(
        evidence,
        limit=6,
        minimum_per_source=1,
    )

    source_types = {
        item.source_type
        for item in selected
    }

    assert "github" in source_types
    assert "notion" in source_types
    assert "code" in source_types


def test_collect_page_titles_is_conservative():
    payload = {
        "results": [
            {
                "title": "Documentation",
                "url": "https://example",
            },
            {
                "page_title": "E.V.I.E. Assistant",
            },
        ]
    }

    titles = _collect_page_titles(
        payload
    )

    assert "Documentation" in titles
    assert "E.V.I.E. Assistant" in titles
