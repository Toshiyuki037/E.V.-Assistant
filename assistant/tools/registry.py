"""
E.V.I.E. - Tool Registry

Created: August 9, 2026
Last Edited: August 10, 2026
Author: Max Maehara

Purpose:
    Maintains the authoritative registry of actions E.V.I.E. may request.

How It Works:
    Every tool has:
    - unique name
    - description
    - category
    - base risk level
    - callable implementation

Important:
    Tool modules register themselves against the canonical
    assistant.tools.registry module.

Most Recent Change:
    Added the Phase 9 integration gateway while preserving the existing
    Phase 6 registry architecture.
"""

from __future__ import annotations

from dataclasses import (
    dataclass,
)

from typing import (
    Callable,
)


# ---------------------------------------------------------------------------
# Tool Definition
# ---------------------------------------------------------------------------

@dataclass
class ToolDefinition:
    name: str

    description: str

    category: str

    risk: str

    function: Callable


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

_TOOL_REGISTRY: dict[
    str,
    ToolDefinition,
] = {}


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def register_tool(
    name: str,
    description: str,
    category: str,
    risk: str,
    function: Callable,
):
    normalized_name = (
        name
        .strip()
        .lower()
    )


    if not normalized_name:

        raise ValueError(
            "Tool name cannot be empty."
        )


    if risk not in {
        "low",
        "medium",
        "high",
    }:

        raise ValueError(
            f"Invalid tool risk: {risk}"
        )


    # -----------------------------------------------------------------------
    # Safe / Idempotent Registration
    # -----------------------------------------------------------------------

    if (
        normalized_name
        in _TOOL_REGISTRY
    ):

        return _TOOL_REGISTRY[
            normalized_name
        ]


    definition = ToolDefinition(
        name=
            normalized_name,

        description=
            description,

        category=
            category,

        risk=
            risk,

        function=
            function,
    )


    _TOOL_REGISTRY[
        normalized_name
    ] = definition


    return definition


# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------

def get_tool(
    name: str,
):
    return _TOOL_REGISTRY.get(
        name
        .strip()
        .lower()
    )


def list_tools():
    return sorted(
        _TOOL_REGISTRY.values(),

        key=lambda tool: (
            tool.category,
            tool.name,
        ),
    )


def tool_exists(
    name: str,
):
    return (
        name
        .strip()
        .lower()

        in _TOOL_REGISTRY
    )


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------

def describe_tools():
    tools = list_tools()


    if not tools:

        return (
            "No E.V.I.E. tools registered."
        )


    blocks = []


    for tool in tools:

        blocks.append(
            (
                f"{tool.name}\n"
                f"  Category: {tool.category}\n"
                f"  Risk: {tool.risk}\n"
                f"  Description: "
                f"{tool.description}"
            )
        )


    return "\n\n".join(
        blocks
    )


# ---------------------------------------------------------------------------
# Default Tool Loading
# ---------------------------------------------------------------------------

def load_default_tools():
    """
    Imports all current E.V.I.E. tool modules.

    When this module is imported normally as assistant.tools.registry,
    each imported module registers itself into this registry.
    """

    # -----------------------------------------------------------------------
    # Phase 6 Core
    # -----------------------------------------------------------------------

    from . import filesystem
    from . import filesystem_search
    from . import terminal

    from . import git
    from . import applications
    from . import browser
    from . import vscode

    # -----------------------------------------------------------------------
    # Phase 13 Unified Computer Control
    # -----------------------------------------------------------------------

    from . import computer


    # -----------------------------------------------------------------------
    # Phase 9 Connected Services
    # -----------------------------------------------------------------------

    from . import integrations


# ---------------------------------------------------------------------------
# Standalone Test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    """
    Important:

    python -m assistant.tools.registry executes this source file under
    the name __main__.

    Tool modules import assistant.tools.registry by its canonical
    package name, so their registrations go into that canonical module.

    Therefore the CLI deliberately imports and uses the canonical
    module instead of inspecting __main__'s separate registry object.
    """

    import importlib


    canonical_registry = (
        importlib.import_module(
            "assistant.tools.registry"
        )
    )


    tools = (
        canonical_registry
        .load_default_tools()
    )


    print(
        "E.V.I.E. Tool Registry"
    )


    print(
        "-----------------------"
    )


    print(
        "Tools registered:",
        len(
            tools
        ),
    )


    print()


    print(
        canonical_registry
        .describe_tools()
    )