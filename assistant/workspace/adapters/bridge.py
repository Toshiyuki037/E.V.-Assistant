"""
E.V.I.E. - Workspace Bridge Utilities

Phase 12E

Purpose:
Safely bridge older E.V.I.E. subsystems into the unified workspace
without hard-coding one historical function signature.

All imports are lazy. Missing optional subsystems fail closed and return
no evidence instead of breaking the whole workspace query.
"""

from __future__ import annotations

import inspect
import json
from importlib import import_module


def stringify(value):
    try:
        return json.dumps(
            value,
            indent=2,
            ensure_ascii=False,
            default=str,
        )
    except Exception:
        return str(value)


def call_first_available(
    module_name: str,
    function_names: list[str],
    query: str,
    *,
    limit: int = 20,
):
    try:
        module = import_module(
            module_name
        )
    except Exception:
        return None

    for name in function_names:
        function = getattr(
            module,
            name,
            None,
        )

        if not callable(
            function
        ):
            continue

        try:
            signature = inspect.signature(
                function
            )

            kwargs = {}

            if "query" in signature.parameters:
                kwargs["query"] = query
            elif "text" in signature.parameters:
                kwargs["text"] = query
            elif "user_query" in signature.parameters:
                kwargs["user_query"] = query

            if "limit" in signature.parameters:
                kwargs["limit"] = limit
            elif "top_k" in signature.parameters:
                kwargs["top_k"] = limit
            elif "k" in signature.parameters:
                kwargs["k"] = limit

            if kwargs:
                return function(
                    **kwargs
                )

            return function(
                query
            )

        except Exception:
            continue

    return None


def flatten_records(
    value,
):
    """
    Convert common subsystem return shapes into a list of records.
    """

    if value is None:
        return []

    if isinstance(
        value,
        list,
    ):
        return value

    if isinstance(
        value,
        tuple,
    ):
        return list(
            value
        )

    if isinstance(
        value,
        dict,
    ):
        for key in (
            "results",
            "items",
            "memories",
            "documents",
            "records",
            "evidence",
        ):
            child = value.get(
                key
            )

            if isinstance(
                child,
                list,
            ):
                return child

        return [
            value
        ]

    return [
        value
    ]


def extract_text(
    value,
):
    if isinstance(
        value,
        str,
    ):
        return value

    if isinstance(
        value,
        dict,
    ):
        for key in (
            "content",
            "text",
            "memory",
            "summary",
            "body",
            "document",
            "chunk",
            "message",
        ):
            child = value.get(
                key
            )

            if isinstance(
                child,
                str,
            ) and child.strip():
                return child

    return stringify(
        value
    )
