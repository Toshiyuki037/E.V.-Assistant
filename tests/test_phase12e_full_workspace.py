"""
Phase 12E full knowledge workspace tests.
"""

from assistant.workspace.adapters.bridge import (
    extract_text,
    flatten_records,
)
from assistant.workspace.adapters.registry import (
    load_default_adapters,
)


def test_full_adapter_registry():
    adapters = load_default_adapters()

    for name in (
        "local",
        "github",
        "notion",
        "repository",
        "memory",
        "knowledge",
        "documents",
        "connected",
    ):
        assert name in adapters


def test_bridge_flattens_common_result_shape():
    records = flatten_records(
        {
            "results": [
                {
                    "text":
                        "hello"
                }
            ]
        }
    )

    assert len(
        records
    ) == 1


def test_bridge_extracts_text():
    assert (
        extract_text(
            {
                "content":
                    "workspace evidence"
            }
        )
        == "workspace evidence"
    )
