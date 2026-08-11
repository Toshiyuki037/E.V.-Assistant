"""
E.V.I.E. - Contextual Reference Resolver

Phase 10C

Purpose:
    Resolves contextual follow-up requests against Phase 10B
    short-term conversation state.

Examples:

    What's the forecast for Honolulu?
    What about Corvallis?

        -> preserve weather.forecast
        -> replace location with Corvallis

    Show commits for E.V.-Assistant.
    What about issues?

        -> preserve repository
        -> change github.commits to github.issues

    Read my Documentation page.
    What about Phase 8?

        -> preserve page
        -> replace section with Phase 8

This module does not execute tools.
It only resolves conversational references.
"""

from __future__ import annotations

import re
from copy import deepcopy

from .context import (
    get_planner_conversation_context,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clean_text(
    value: str,
):
    return (
        str(
            value
            or ""
        )
        .strip()
    )


def _lower(
    value: str,
):
    return (
        _clean_text(
            value
        )
        .lower()
    )


def _base_integration_request(
    context: dict,
):
    """
    Reconstruct the previous integration request.
    """

    if not context:

        return None


    if (
        context.get(
            "last_tool"
        )
        != "integration_execute"
    ):

        return None


    capability = (
        context.get(
            "last_capability"
        )
        or ""
    )


    provider = (
        context.get(
            "last_provider"
        )
        or ""
    )


    if not capability or not provider:

        return None


    result = {
        "capability":
            capability,

        "provider":
            provider,
    }


    account_id = (
        context.get(
            "last_account_id"
        )
        or ""
    )


    if account_id:

        result[
            "account_id"
        ] = account_id


    routing_mode = (
        context.get(
            "last_routing_mode"
        )
        or ""
    )


    if routing_mode:

        result[
            "routing_mode"
        ] = routing_mode


    previous_arguments = (
        context.get(
            "last_arguments"
        )
        or {}
    )


    if isinstance(
        previous_arguments,
        dict,
    ):

        result[
            "arguments"
        ] = deepcopy(
            previous_arguments
        )


    else:

        result[
            "arguments"
        ] = {}


    return result


# ---------------------------------------------------------------------------
# Section Resolution
# ---------------------------------------------------------------------------

def _extract_phase(
    text: str,
):
    match = re.search(
        r"\bphase\s+([0-9]+[a-z]?)\b",
        text,
        flags=re.IGNORECASE,
    )


    if not match:

        return None


    return (
        "Phase "
        + match.group(1).upper()
    )


# ---------------------------------------------------------------------------
# Weather Resolution
# ---------------------------------------------------------------------------

def _resolve_weather(
    text: str,
    request: dict,
):
    lowered = (
        text.lower()
    )


    arguments = (
        request.setdefault(
            "arguments",
            {},
        )
    )


    # -----------------------------------------------------------------------
    # Temporal changes
    # -----------------------------------------------------------------------

    if (
        "tomorrow"
        in lowered
    ):

        request[
            "capability"
        ] = "weather.forecast"

        arguments[
            "days"
        ] = 2


    elif (
        "this week"
        in lowered
        or "7 day"
        in lowered
        or "7-day"
        in lowered
    ):

        request[
            "capability"
        ] = "weather.forecast"

        arguments[
            "days"
        ] = 7


    elif (
        "forecast"
        in lowered
    ):

        request[
            "capability"
        ] = "weather.forecast"


    elif (
        "current weather"
        in lowered
        or "weather right now"
        in lowered
    ):

        request[
            "capability"
        ] = "weather.current"

        arguments.pop(
            "days",
            None,
        )


    # -----------------------------------------------------------------------
    # "What about LOCATION?"
    # -----------------------------------------------------------------------

    match = re.match(
        r"^\s*(?:what|how)\s+about\s+(.+?)\s*[?.!]*$",
        text,
        flags=re.IGNORECASE,
    )


    if match:

        candidate = (
            match.group(1)
            .strip()
            .rstrip("?.!")
            .strip()
        )


        reserved = {
            "tomorrow",
            "today",
            "this week",
            "next week",
            "there",
        }


        if (
            candidate
            and candidate.lower()
            not in reserved
            and not candidate.lower().startswith(
                "phase "
            )
        ):

            arguments[
                "location"
            ] = candidate


    return request


# ---------------------------------------------------------------------------
# GitHub Resolution
# ---------------------------------------------------------------------------

def _resolve_github(
    text: str,
    request: dict,
):
    lowered = (
        text.lower()
    )


    capability_map = {
        "commit":
            "github.commits",

        "commits":
            "github.commits",

        "issue":
            "github.issues",

        "issues":
            "github.issues",

        "pull request":
            "github.pulls",

        "pull requests":
            "github.pulls",

        "pulls":
            "github.pulls",

        "actions":
            "github.actions",

        "workflow":
            "github.workflows",

        "workflows":
            "github.workflows",

        "repositories":
            "github.repos",

        "repos":
            "github.repos",
    }


    for phrase, capability in capability_map.items():

        if re.search(
            r"\b"
            + re.escape(
                phrase
            )
            + r"\b",
            lowered,
        ):

            request[
                "capability"
            ] = capability

            break


    return request


# ---------------------------------------------------------------------------
# Notion Resolution
# ---------------------------------------------------------------------------

def _resolve_notion(
    text: str,
    request: dict,
):
    lowered = (
        text.lower()
    )


    arguments = (
        request.setdefault(
            "arguments",
            {},
        )
    )


    phase = (
        _extract_phase(
            text
        )
    )


    if phase:

        request[
            "capability"
        ] = "notion.read_document"

        arguments[
            "section"
        ] = phase


    if (
        "read"
        in lowered
        and request.get(
            "capability"
        )
        == "notion.document"
    ):

        request[
            "capability"
        ] = "notion.read_document"


    return request


# ---------------------------------------------------------------------------
# Finance Resolution
# ---------------------------------------------------------------------------

def _resolve_finance(
    text: str,
    request: dict,
):
    lowered = (
        text.lower()
    )


    arguments = (
        request.setdefault(
            "arguments",
            {},
        )
    )


    symbol_aliases = {
        "tesla":
            "TSLA",

        "nvidia":
            "NVDA",

        "apple":
            "AAPL",

        "microsoft":
            "MSFT",

        "amazon":
            "AMZN",

        "google":
            "GOOGL",

        "alphabet":
            "GOOGL",

        "meta":
            "META",
    }


    for name, symbol in symbol_aliases.items():

        if re.search(
            r"\b"
            + re.escape(
                name
            )
            + r"\b",
            lowered,
        ):

            arguments[
                "symbol"
            ] = symbol

            break


    return request


# ---------------------------------------------------------------------------
# Account Reference
# ---------------------------------------------------------------------------

def _resolve_account_reference(
    text: str,
    request: dict,
):
    lowered = (
        text.lower()
    )


    if (
        "other account"
        not in lowered
    ):

        return request


    # Do not guess which account.
    #
    # Tell the planner/router that another account must be selected.

    request.pop(
        "account_id",
        None,
    )


    request[
        "routing_mode"
    ] = "single_best"


    request[
        "_contextual_account_request"
    ] = "other"


    return request


# ---------------------------------------------------------------------------
# Main Resolver
# ---------------------------------------------------------------------------

def resolve_contextual_request(
    user_message: str,
):
    """
    Resolve a contextual follow-up against Phase 10B state.

    Returns:
        dict | None

    None means:
        The resolver could not safely determine a contextual request.
    """

    text = (
        _clean_text(
            user_message
        )
    )


    if not text:

        return None


    context = (
        get_planner_conversation_context()
    )


    if not context:

        return None


    request = (
        _base_integration_request(
            context
        )
    )


    if request is None:

        return None


    provider = (
        _lower(
            request.get(
                "provider"
            )
        )
    )


    # -----------------------------------------------------------------------
    # Provider-Specific Resolution
    # -----------------------------------------------------------------------

    if (
        provider
        == "weather"
    ):

        request = (
            _resolve_weather(
                text,
                request,
            )
        )


    elif (
        provider
        == "github"
    ):

        request = (
            _resolve_github(
                text,
                request,
            )
        )


    elif (
        provider
        == "notion"
    ):

        request = (
            _resolve_notion(
                text,
                request,
            )
        )


    elif (
        provider
        in {
            "schwab",
            "finance",
        }
    ):

        request = (
            _resolve_finance(
                text,
                request,
            )
        )


    # -----------------------------------------------------------------------
    # Cross-provider account reference
    # -----------------------------------------------------------------------

    request = (
        _resolve_account_reference(
            text,
            request,
        )
    )


    return request


# ---------------------------------------------------------------------------
# Standalone Diagnostic
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    from .context import (
        clear_conversation_state,
        record_tool_context,
    )


    clear_conversation_state()


    record_tool_context(
        "integration_execute",

        {
            "capability":
                "weather.forecast",

            "provider":
                "weather",

            "account_id":
                "public",

            "routing_mode":
                "explicit_account",

            "arguments": {
                "location":
                    "Honolulu",

                "days":
                    7,
            },
        },

        "What's the forecast for Honolulu?",
    )


    print(
        resolve_contextual_request(
            "What about Corvallis?"
        )
    )