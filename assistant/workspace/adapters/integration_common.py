"""
E.V.I.E. - Connected Integration Adapter Helpers

Phase 12B
"""

from __future__ import annotations

import json
from typing import Any

from assistant.tools.executor import execute_tool


def execute_integration(
    *,
    capability: str,
    provider: str,
    account_id: str,
    arguments: dict[str, Any] | None = None,
):
    payload = {
        "capability": capability,
        "provider": provider,
        "account_id": account_id,
        "routing_mode": "explicit_account",
    }

    if arguments:
        payload["arguments"] = arguments

    result = execute_tool(
        "integration_execute",
        payload,
    )

    return result


def extract_evidence_data(
    execution_result,
):
    if not isinstance(
        execution_result,
        dict,
    ):
        return []

    result = execution_result.get(
        "result"
    )

    if not isinstance(
        result,
        dict,
    ):
        return []

    evidence = (
        result.get(
            "evidence",
            []
        )
        or []
    )

    return [
        item
        for item in evidence
        if isinstance(
            item,
            dict,
        )
    ]


def stringify_payload(
    value,
):
    try:
        return json.dumps(
            value,
            indent=2,
            ensure_ascii=False,
            default=str,
        )
    except Exception:
        return str(value)
